"""Implementation of a Threaded Modbus Server."""
# pylint: disable=missing-type-doc
from __future__ import annotations

import asyncio
import os
import traceback
from contextlib import suppress

from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock, ModbusDeviceIdentification
from pymodbus.exceptions import ModbusException, NoSuchSlaveException
from pymodbus.framer import FRAMER_NAME_TO_CLASS, FramerBase, FramerType
from pymodbus.logging import Log
from pymodbus.pdu import DecodePDU
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.pdu.pdu import ExceptionResponse
from pymodbus.transport import CommParams, CommType, ModbusProtocol


# --------------------------------------------------------------------------- #
# Protocol Handlers
# --------------------------------------------------------------------------- #


class ModbusServerRequestHandler(ModbusProtocol):
    """Implements modbus slave wire protocol.

    This uses the asyncio.Protocol to implement the server protocol.

    When a connection is established, a callback is called.
    This callback will setup the connection and
    create and schedule an asyncio.Task and assign it to running_task.
    """

    def __init__(self, owner):
        """Initialize."""
        params = CommParams(
            comm_name="server",
            comm_type=owner.comm_params.comm_type,
            reconnect_delay=0.0,
            reconnect_delay_max=0.0,
            timeout_connect=0.0,
            host=owner.comm_params.source_address[0],
            port=owner.comm_params.source_address[1],
        )
        super().__init__(params, True)
        self.server = owner
        self.running = False
        self.receive_queue: asyncio.Queue = asyncio.Queue()
        self.handler_task = None  # coroutine to be run on asyncio loop
        self.databuffer = b''
        self.framer: FramerBase
        self.loop = asyncio.get_running_loop()

    def _log_exception(self):
        """Show log exception."""
        Log.debug(
            "Handler for stream [{}] has been canceled", self.comm_params.comm_name
        )

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        Log.debug("callback_new_connection called")
        return ModbusServerRequestHandler(self)

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""
        slaves = self.server.context.slaves()
        if self.server.broadcast_enable:
            if 0 not in slaves:
                slaves.append(0)
        try:
            self.running = True
            self.framer = self.server.framer(self.server.decoder)

            # schedule the connection handler on the event loop
            self.handler_task = asyncio.create_task(self.handle())
            self.handler_task.set_name("server connection handler")
        except Exception as exc:  # pylint: disable=broad-except
            Log.error(
                "Server callback_connected exception: {}; {}",
                exc,
                traceback.format_exc(),
            )

    def callback_disconnected(self, call_exc: Exception | None) -> None:
        """Call when connection is lost."""
        try:
            if self.handler_task:
                self.handler_task.cancel()
            if hasattr(self.server, "on_connection_lost"):
                self.server.on_connection_lost()
            if call_exc is None:
                self._log_exception()
            else:
                Log.debug(
                    "Client Disconnection {} due to {}",
                    self.comm_params.comm_name,
                    call_exc,
                )
            self.running = False
        except Exception as exc:  # pylint: disable=broad-except
            Log.error(
                "Datastore unable to fulfill request: {}; {}",
                exc,
                traceback.format_exc(),
            )

    async def inner_handle(self):
        """Handle handler."""
        # this is an asyncio.Queue await, it will never fail
        data = await self._recv_()
        if isinstance(data, tuple):
            # addr is populated when talking over UDP
            data, *addr = data
        else:
            addr = [None]

        # if broadcast is enabled make sure to
        # process requests to address 0
        self.databuffer += data
        Log.debug("Handling data: {}", self.databuffer, ":hex")
        try:
            used_len, pdu = self.framer.processIncomingFrame(self.databuffer)
        except ModbusException:
            pdu = ExceptionResponse(
                40,
                exception_code=merror.IllegalFunction
            )
            self.server_send(pdu, 0)
            pdu = None
            used_len = len(self.databuffer)
        self.databuffer = self.databuffer[used_len:]
        if pdu:
           self.execute(pdu, *addr)

    async def handle(self) -> None:
        """Coroutine which represents a single master <=> slave conversation.

        Once the client connection is established, the data chunks will be
        fed to this coroutine via the asyncio.Queue object which is fed by
        the ModbusServerRequestHandler class's callback Future.

        This callback future gets data from either asyncio.BaseProtocol.data_received
        or asyncio.DatagramProtocol.datagram_received.

        This function will execute without blocking in the while-loop and
        yield to the asyncio event loop when the frame is exhausted.
        As a result, multiple clients can be interleaved without any
        interference between them.
        """
        while self.running:
            try:
                await self.inner_handle()
            except asyncio.CancelledError:
                # catch and ignore cancellation errors
                if self.running:
                    self._log_exception()
                    self.running = False
            except Exception as exc:  # pylint: disable=broad-except
                # force TCP socket termination as framer
                # should handle application layer errors
                Log.error(
                    'Unknown exception "{}" on stream {} forcing disconnect',
                    exc,
                    self.comm_params.comm_name,
                )
                self.close()
                self.callback_disconnected(exc)

    def execute(self, request, *addr):
        """Call with the resulting message.

        :param request: The decoded request message
        :param addr: the address
        """
        if self.server.request_tracer:
            self.server.request_tracer(request, *addr)

        asyncio.run_coroutine_threadsafe(self._async_execute(request, *addr), self.loop)

    async def _async_execute(self, request, *addr):
        broadcast = False
        try:
            if self.server.broadcast_enable and not request.slave_id:
                broadcast = True
                # if broadcasting then execute on all slave contexts,
                # note response will be ignored
                for slave_id in self.server.context.slaves():
                    response = await request.update_datastore(self.server.context[slave_id])
            else:
                context = self.server.context[request.slave_id]
                response = await request.update_datastore(context)

        except NoSuchSlaveException:
            Log.error("requested slave does not exist: {}", request.slave_id)
            if self.server.ignore_missing_slaves:
                return  # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as exc:  # pylint: disable=broad-except
            Log.error(
                "Datastore unable to fulfill request: {}; {}",
                exc,
                traceback.format_exc(),
            )
            response = request.doException(merror.SlaveFailure)
        # no response when broadcasting
        if not broadcast:
            response.transaction_id = request.transaction_id
            response.slave_id = request.slave_id
            skip_encoding = False
            if self.server.response_manipulator:
                response, skip_encoding = self.server.response_manipulator(response)
            self.server_send(response, *addr, skip_encoding=skip_encoding)

    def server_send(self, message, addr, **kwargs):
        """Send message."""
        if kwargs.get("skip_encoding", False):
            self.send(message, addr=addr)
        if not message:
            Log.debug("Skipping sending response!!")
        else:
            pdu = self.framer.buildFrame(message)
            self.send(pdu, addr=addr)

    async def _recv_(self):
        """Receive data from the network."""
        try:
            result = await self.receive_queue.get()
        except RuntimeError:
            Log.error("Event loop is closed")
            result = None
        return result

    def callback_data(self, data: bytes, addr: tuple | None = ()) -> int:
        """Handle received data."""
        if addr != ():
            self.receive_queue.put_nowait((data, addr))
        else:
            self.receive_queue.put_nowait(data)
        return len(data)


# --------------------------------------------------------------------------- #
# Server Implementations
# --------------------------------------------------------------------------- #


class ModbusBaseServer(ModbusProtocol):
    """Common functionality for all server classes."""

    def __init__(
        self,
        params: CommParams,
        context,
        ignore_missing_slaves,
        broadcast_enable,
        response_manipulator,
        request_tracer,
        identity,
        framer,
    ) -> None:
        """Initialize base server."""
        super().__init__(
            params,
            True,
        )
        self.loop = asyncio.get_running_loop()
        self.decoder = DecodePDU(True)
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.ignore_missing_slaves = ignore_missing_slaves
        self.broadcast_enable = broadcast_enable
        self.response_manipulator = response_manipulator
        self.request_tracer = request_tracer
        self.handle_local_echo = False
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        self.framer = FRAMER_NAME_TO_CLASS[framer]
        self.serving: asyncio.Future = asyncio.Future()

    def callback_new_connection(self):
        """Handle incoming connect."""
        return ModbusServerRequestHandler(self)

    async def shutdown(self):
        """Close server."""
        if not self.serving.done():
            self.serving.set_result(True)
        self.close()

    async def serve_forever(self):
        """Start endless loop."""
        if self.transport:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )
        await self.listen()
        Log.info("Server listening.")
        await self.serving
        Log.info("Server graceful shutdown.")

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""
        Log.debug("callback_disconnected called: {}", exc)

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        Log.debug("callback_data called: {} addr={}", data, ":hex", addr)
        return 0

class ModbusTcpServer(ModbusBaseServer):
    """A modbus threaded tcp socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(
        self,
        context,
        framer=FramerType.SOCKET,
        identity=None,
        address=("", 502),
        ignore_missing_slaves=False,
        broadcast_enable=False,
        response_manipulator=None,
        request_tracer=None,
    ):
        """Initialize the socket server.

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat slave_id 0 as broadcast address,
                        False to treat 0 as any other slave_id
        :param response_manipulator: Callback method for manipulating the
                                        response
        :param request_tracer: Callback method for tracing
        """
        params = getattr(
            self,
            "tls_setup",
            CommParams(
                comm_type=CommType.TCP,
                comm_name="server_listener",
                reconnect_delay=0.0,
                reconnect_delay_max=0.0,
                timeout_connect=0.0,
            ),
        )
        params.source_address = address
        super().__init__(
            params,
            context,
            ignore_missing_slaves,
            broadcast_enable,
            response_manipulator,
            request_tracer,
            identity,
            framer,
        )


class ModbusTlsServer(ModbusTcpServer):
    """A modbus threaded tls socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        context,
        framer=FramerType.TLS,
        identity=None,
        address=("", 502),
        sslctx=None,
        certfile=None,
        keyfile=None,
        password=None,
        ignore_missing_slaves=False,
        broadcast_enable=False,
        response_manipulator=None,
        request_tracer=None,
    ):
        """Overloaded initializer for the socket server.

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param sslctx: The SSLContext to use for TLS (default None and auto
                       create)
        :param certfile: The cert file path for TLS (used if sslctx is None)
        :param keyfile: The key file path for TLS (used if sslctx is None)
        :param password: The password for for decrypting the private key file
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat slave_id 0 as broadcast address,
                        False to treat 0 as any other slave_id
        :param response_manipulator: Callback method for
                        manipulating the response
        """
        self.tls_setup = CommParams(
            comm_type=CommType.TLS,
            comm_name="server_listener",
            reconnect_delay=0.0,
            reconnect_delay_max=0.0,
            timeout_connect=0.0,
            sslctx=CommParams.generate_ssl(
                True, certfile, keyfile, password, sslctx=sslctx
            ),
        )
        super().__init__(
            context,
            framer=framer,
            identity=identity,
            address=address,
            ignore_missing_slaves=ignore_missing_slaves,
            broadcast_enable=broadcast_enable,
            response_manipulator=response_manipulator,
            request_tracer=request_tracer,
        )


class ModbusUdpServer(ModbusBaseServer):
    """A modbus threaded udp socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(
        self,
        context,
        framer=FramerType.SOCKET,
        identity=None,
        address=("", 502),
        ignore_missing_slaves=False,
        broadcast_enable=False,
        response_manipulator=None,
        request_tracer=None,
    ):
        """Overloaded initializer for the socket server.

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param ignore_missing_slaves: True to not send errors on a request
                            to a missing slave
        :param broadcast_enable: True to treat slave_id 0 as broadcast address,
                            False to treat 0 as any other slave_id
        :param response_manipulator: Callback method for
                            manipulating the response
        :param request_tracer: Callback method for tracing
        """
        # ----------------
        super().__init__(
            CommParams(
                comm_type=CommType.UDP,
                comm_name="server_listener",
                source_address=address,
                reconnect_delay=0.0,
                reconnect_delay_max=0.0,
                timeout_connect=0.0,
            ),
            context,
            ignore_missing_slaves,
            broadcast_enable,
            response_manipulator,
            request_tracer,
            identity,
            framer,
        )


class ModbusSerialServer(ModbusBaseServer):
    """A modbus threaded serial socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(
        self, context, framer=FramerType.RTU, identity=None, **kwargs
    ):
        """Initialize the socket server.

        If the identity structure is not passed in, the ModbusControlBlock
        uses its own empty structure.
        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use, default FramerType.RTU
        :param identity: An optional identify structure
        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout to use for the serial device
        :param handle_local_echo: (optional) Discard local echo from dongle.
        :param ignore_missing_slaves: True to not send errors on a request
                            to a missing slave
        :param broadcast_enable: True to treat slave_id 0 as broadcast address,
                            False to treat 0 as any other slave_id
        :param reconnect_delay: reconnect delay in seconds
        :param response_manipulator: Callback method for
                    manipulating the response
        :param request_tracer: Callback method for tracing
        """
        super().__init__(
            params=CommParams(
                comm_type=CommType.SERIAL,
                comm_name="server_listener",
                reconnect_delay=kwargs.get("reconnect_delay", 2),
                reconnect_delay_max=0.0,
                timeout_connect=kwargs.get("timeout", 3),
                source_address=(kwargs.get("port", 0), 0),
                bytesize=kwargs.get("bytesize", 8),
                parity=kwargs.get("parity", "N"),
                baudrate=kwargs.get("baudrate", 19200),
                stopbits=kwargs.get("stopbits", 1),
            ),
            context=context,
            ignore_missing_slaves=kwargs.get("ignore_missing_slaves", False),
            broadcast_enable=kwargs.get("broadcast_enable", False),
            response_manipulator=kwargs.get("response_manipulator", None),
            request_tracer=kwargs.get("request_tracer", None),
            identity=kwargs.get("identity", None),
            framer=framer,
        )
        self.handle_local_echo = kwargs.get("handle_local_echo", False)


# --------------------------------------------------------------------------- #
# Creation Factories
# --------------------------------------------------------------------------- #


class _serverList:
    """Maintains information about the active server.

    :meta private:
    """

    active_server: ModbusTcpServer | ModbusUdpServer | ModbusSerialServer

    def __init__(self, server):
        """Register new server."""
        self.server = server
        self.loop = asyncio.get_event_loop()

    @classmethod
    async def run(cls, server, custom_functions) -> None:
        """Help starting/stopping server."""
        for func in custom_functions:
            server.decoder.register(func)
        cls.active_server = _serverList(server)  # type: ignore[assignment]
        with suppress(asyncio.exceptions.CancelledError):
            await server.serve_forever()

    @classmethod
    async def async_stop(cls) -> None:
        """Wait for server stop."""
        if not cls.active_server:
            raise RuntimeError("ServerAsyncStop called without server task active.")
        await cls.active_server.server.shutdown()  # type: ignore[union-attr]
        cls.active_server = None  # type: ignore[assignment]

    @classmethod
    def stop(cls):
        """Wait for server stop."""
        if not cls.active_server:
            Log.info("ServerStop called without server task active.")
            return
        if not cls.active_server.loop.is_running():
            Log.info("ServerStop called with loop stopped.")
            return
        future = asyncio.run_coroutine_threadsafe(cls.async_stop(), cls.active_server.loop)
        future.result(timeout=10 if os.name == 'nt' else 0.1)


async def StartAsyncTcpServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    address=None,
    custom_functions=[],
    **kwargs,
):
    """Start and run a tcp modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param kwargs: The rest
    """
    kwargs.pop("host", None)
    server = ModbusTcpServer(
        context, kwargs.pop("framer", FramerType.SOCKET), identity, address, **kwargs
    )
    await _serverList.run(server, custom_functions)


async def StartAsyncTlsServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    address=None,
    sslctx=None,
    certfile=None,
    keyfile=None,
    password=None,
    custom_functions=[],
    **kwargs,
):
    """Start and run a tls modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param sslctx: The SSLContext to use for TLS (default None and auto create)
    :param certfile: The cert file path for TLS (used if sslctx is None)
    :param keyfile: The key file path for TLS (used if sslctx is None)
    :param password: The password for for decrypting the private key file
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param kwargs: The rest
    """
    kwargs.pop("host", None)
    server = ModbusTlsServer(
        context,
        kwargs.pop("framer", FramerType.TLS),
        identity,
        address,
        sslctx,
        certfile,
        keyfile,
        password,
        **kwargs,
    )
    await _serverList.run(server, custom_functions)


async def StartAsyncUdpServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    address=None,
    custom_functions=[],
    **kwargs,
):
    """Start and run a udp modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param kwargs:
    """
    kwargs.pop("host", None)
    server = ModbusUdpServer(
        context, kwargs.pop("framer", FramerType.SOCKET), identity, address, **kwargs
    )
    await _serverList.run(server, custom_functions)


async def StartAsyncSerialServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    custom_functions=[],
    **kwargs,
):
    """Start and run a serial modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param kwargs: The rest
    """
    server = ModbusSerialServer(
        context, kwargs.pop("framer", FramerType.RTU), identity=identity, **kwargs
    )
    await _serverList.run(server, custom_functions)


def StartSerialServer(**kwargs):  # pylint: disable=invalid-name
    """Start and run a serial modbus server."""
    return asyncio.run(StartAsyncSerialServer(**kwargs))


def StartTcpServer(**kwargs):  # pylint: disable=invalid-name
    """Start and run a serial modbus server."""
    return asyncio.run(StartAsyncTcpServer(**kwargs))


def StartTlsServer(**kwargs):  # pylint: disable=invalid-name
    """Start and run a serial modbus server."""
    return asyncio.run(StartAsyncTlsServer(**kwargs))


def StartUdpServer(**kwargs):  # pylint: disable=invalid-name
    """Start and run a serial modbus server."""
    return asyncio.run(StartAsyncUdpServer(**kwargs))


async def ServerAsyncStop():  # pylint: disable=invalid-name
    """Terminate server."""
    await _serverList.async_stop()


def ServerStop():  # pylint: disable=invalid-name
    """Terminate server."""
    _serverList.stop()
