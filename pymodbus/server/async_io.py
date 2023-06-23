"""Implementation of a Threaded Modbus Server."""
# pylint: disable=missing-type-doc
import asyncio
import time
import traceback
from contextlib import suppress
from typing import Union

from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock, ModbusDeviceIdentification
from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.factory import ServerDecoder
from pymodbus.framer import ModbusFramer
from pymodbus.logging import Log
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)
from pymodbus.transport.transport import CommParams, CommType, Transport


with suppress(ImportError):
    pass


# --------------------------------------------------------------------------- #
# Protocol Handlers
# --------------------------------------------------------------------------- #


class ModbusServerRequestHandler(Transport):
    """Implements modbus slave wire protocol.

    This uses the asyncio.Protocol to implement the server protocol.

    When a connection is established, the asyncio.Protocol.connection_made
    callback is called. This callback will setup the connection and
    create and schedule an asyncio.Task and assign it to running_task.

    running_task will be canceled upon connection_lost event.
    """

    def __init__(self, owner):
        """Initialize."""
        params = CommParams(
            comm_name="server",
            reconnect_delay=0.0,
            reconnect_delay_max=0.0,
            timeout_connect=0.0,
            host=owner.comm_params.host,
            port=owner.comm_params.port,
        )
        super().__init__(params, True)
        self.server = owner
        self.running = False
        self.receive_queue = asyncio.Queue()
        self.handler_task = None  # coroutine to be run on asyncio loop
        self._sent = b""  # for handle_local_echo
        self.client_address = (None, None)
        self.framer: ModbusFramer = None

    def _log_exception(self):
        """Show log exception."""
        Log.debug("Handler for stream [{}] has been canceled", self.client_address)

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""
        try:
            if (
                hasattr(self.transport, "get_extra_info")
                and self.transport.get_extra_info("peername") is not None
            ):
                self.client_address = self.transport.get_extra_info("peername")[:2]
                Log.debug("Peer [{}] opened", self.client_address)
            elif hasattr(self.transport, "serial"):
                Log.debug(
                    "Serial connection opened on port: {}", self.transport.serial.port
                )
                self.client_address = ("serial", "server")
            else:
                Log.warning(
                    "Unable to get information about transport {}", self.transport
                )
            self.transport = self.transport
            self.running = True
            self.framer = self.server.framer(
                self.server.decoder,
                client=None,
            )
            self.server.local_active_connections[self.client_address] = self

            # schedule the connection handler on the event loop
            self.handler_task = asyncio.create_task(self.handle())
        except Exception as exc:  # pragma: no cover pylint: disable=broad-except
            Log.error(
                "Server connection_made unable to fulfill request: {}; {}",
                exc,
                traceback.format_exc(),
            )

    def callback_disconnected(self, call_exc: Exception) -> None:
        """Call when connection is lost."""
        try:
            if self.handler_task:
                self.handler_task.cancel()
            if self.client_address in self.server.local_active_connections:
                self.server.local_active_connections.pop(self.client_address)
            if hasattr(self.server, "on_connection_lost"):
                self.server.on_connection_lost()
            if call_exc is None:
                self._log_exception()
            else:
                Log.debug(
                    "Client Disconnection {} due to {}", self.client_address, call_exc
                )
            self.running = False
        except Exception as exc:  # pylint: disable=broad-except
            Log.error(
                "Datastore unable to fulfill request: {}; {}",
                exc,
                traceback.format_exc(),
            )

    async def handle(self):
        """Return Asyncio coroutine which represents a single conversation.

        between the modbus slave and master

        Once the client connection is established, the data chunks will be
        fed to this coroutine via the asyncio.Queue object which is fed by
        the ModbusServerRequestHandler class's callback Future.

        This callback future gets data from either
        asyncio.DatagramProtocol.datagram_received or
        from asyncio.BaseProtocol.data_received.

        This function will execute without blocking in the while-loop and
        yield to the asyncio event loop when the frame is exhausted.
        As a result, multiple clients can be interleaved without any
        interference between them.
        """
        reset_frame = False
        while self.running:
            try:
                slaves = self.server.context.slaves()
                # this is an asyncio.Queue await, it will never fail
                data = await self._recv_()
                if isinstance(data, tuple):
                    # addr is populated when talking over UDP
                    data, *addr = data
                else:
                    addr = (None,)  # empty tuple

                # if broadcast is enabled make sure to
                # process requests to address 0
                if self.server.broadcast_enable:  # pragma: no cover
                    if 0 not in slaves:
                        slaves.append(0)

                Log.debug("Handling data: {}", data, ":hex")

                single = self.server.context.single
                self.framer.processIncomingPacket(
                    data=data,
                    callback=lambda x: self.execute(x, *addr),
                    slave=slaves,
                    single=single,
                )

            except asyncio.CancelledError:
                # catch and ignore cancellation errors
                if self.running:
                    self._log_exception()
                    self.running = False
            except Exception as exc:  # pylint: disable=broad-except
                # force TCP socket termination as processIncomingPacket
                # should handle application layer errors
                # for UDP sockets, simply reset the frame
                if isinstance(self, ModbusServerRequestHandler):
                    client_addr = self.client_address[:2]
                    Log.error(
                        'Unknown exception "{}" on stream {} forcing disconnect',
                        exc,
                        client_addr,
                    )
                    self.transport.close()
                else:
                    Log.error("Unknown error occurred {}", exc)
                    reset_frame = True  # graceful recovery
            finally:
                if reset_frame:
                    self.framer.resetFrame()
                    reset_frame = False

    def execute(self, request, *addr):
        """Call with the resulting message.

        :param request: The decoded request message
        :param addr: the address
        """
        if self.server.request_tracer:
            self.server.request_tracer(request, *addr)

        broadcast = False
        try:
            if self.server.broadcast_enable and not request.slave_id:
                broadcast = True
                # if broadcasting then execute on all slave contexts,
                # note response will be ignored
                for slave_id in self.server.context.slaves():
                    response = request.execute(self.server.context[slave_id])
            else:
                context = self.server.context[request.slave_id]
                response = request.execute(context)
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
            self.send(response, *addr, skip_encoding=skip_encoding)

    def send(self, message, *addr, **kwargs):
        """Send message."""

        def __send(msg, *addr):
            Log.debug("send: [{}]- {}", message, msg, ":b2a")
            if addr == (None,):
                self.transport.write(msg)
                if self.server.handle_local_echo is True:
                    self._sent = msg
            else:
                self.transport.sendto(msg, *addr)

        if kwargs.get("skip_encoding", False):
            __send(message, *addr)
        elif message.should_respond:
            # self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            __send(pdu, *addr)
        else:
            Log.debug("Skipping sending response!!")

    async def _recv_(self):  # pragma: no cover
        """Receive data from the network."""
        try:
            result = await self.receive_queue.get()
        except RuntimeError:
            Log.error("Event loop is closed")
            result = None
        return result

    def callback_data(self, data: bytes, addr: tuple = None) -> int:
        """Handle received data."""
        if self.server.handle_local_echo is True and self._sent:
            if self._sent in data:
                data, self._sent = data.replace(self._sent, b"", 1), b""
            elif self._sent.startswith(data):
                self._sent, data = self._sent.replace(data, b"", 1), b""
            else:
                self._sent = b""
            if not data:
                return 0
        if addr:
            self.receive_queue.put_nowait((data, addr))
        else:
            self.receive_queue.put_nowait(data)
        return len(data)


# --------------------------------------------------------------------------- #
# Server Implementations
# --------------------------------------------------------------------------- #


class ModbusTcpServer(Transport):
    """A modbus threaded tcp socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(
        self,
        context,
        framer=None,
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
        params.host = address[0]
        params.port = address[1]
        super().__init__(
            params,
            True,
        )
        self.local_active_connections = {}
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.ignore_missing_slaves = ignore_missing_slaves
        self.broadcast_enable = broadcast_enable
        self.response_manipulator = response_manipulator
        self.request_tracer = request_tracer
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        # asyncio future that will be done once server has started
        self.serving = asyncio.Future()
        self.serving_done = asyncio.Future()
        # constructors cannot be declared async, so we have to
        # defer the initialization of the server
        self.handle_local_echo = False

    def handle_new_connection(self):
        """Handle incoming connect."""
        return ModbusServerRequestHandler(self)

    async def serve_forever(self):
        """Start endless loop."""
        if self.transport is None:
            await self.transport_listen()
            self.serving.set_result(True)
            Log.info("Server(TCP) listening.")
            try:
                await self.transport.serve_forever()
            except asyncio.exceptions.CancelledError:
                self.serving_done.set_result(False)
                raise
            except Exception as exc:  # pylint: disable=broad-except
                Log.error("Server unexpected exception {}", exc)
        else:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )
        self.serving_done.set_result(True)
        Log.info("Server graceful shutdown.")

    async def shutdown(self):
        """Shutdown server."""
        await self.server_close()

    async def server_close(self):
        """Close server."""
        active_connecions = self.local_active_connections.copy()
        for k_item, v_item in active_connecions.items():
            Log.warning("aborting active session {}", k_item)
            v_item.transport.close()
            await asyncio.sleep(0.1)
            v_item.handler_task.cancel()
            await v_item.handler_task
        self.local_active_connections = {}
        self.transport_close()


class ModbusTlsServer(ModbusTcpServer):
    """A modbus threaded tls socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        context,
        framer=None,
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


class ModbusUdpServer(Transport):
    """A modbus threaded udp socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(
        self,
        context,
        framer=None,
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
        :param handler: A handler for each client session; default is
                            ModbusDisonnectedRequestHandler
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
                host=address[0],
                port=address[1],
                reconnect_delay=0.0,
                reconnect_delay_max=0.0,
                timeout_connect=0.0,
            ),
            True,
        )

        self.local_active_connections = {}
        self.loop = asyncio.get_running_loop()
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.ignore_missing_slaves = ignore_missing_slaves
        self.broadcast_enable = broadcast_enable
        self.response_manipulator = response_manipulator
        self.request_tracer = request_tracer
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)
        self.stop_serving = self.loop.create_future()
        # asyncio future that will be done once server has started
        self.serving = asyncio.Future()
        self.serving_done = asyncio.Future()
        self.request_tracer = None
        self.handle_local_echo = False

    def handle_new_connection(self):
        """Handle incoming connect."""
        return ModbusServerRequestHandler(self)

    async def serve_forever(self):
        """Start endless loop."""
        if self.transport is None:
            try:
                await self.transport_listen()
            except asyncio.exceptions.CancelledError:
                self.serving_done.set_result(False)
                raise
            except Exception as exc:
                Log.error("Server unexpected exception {}", exc)
                self.serving_done.set_result(False)
                raise RuntimeError(exc) from exc
            Log.info("Server(UDP) listening.")
            self.serving.set_result(True)
            await self.stop_serving
        else:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )
        self.serving_done.set_result(True)

    async def shutdown(self):
        """Shutdown server."""
        await self.server_close()

    async def server_close(self):
        """Close server."""
        self.transport_close()
        if not self.stop_serving.done():
            self.stop_serving.set_result(True)


class ModbusSerialServer(Transport):
    """A modbus threaded serial socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(
        self, context, framer=ModbusRtuFramer, identity=None, **kwargs
    ):  # pragma: no cover
        """Initialize the socket server.

        If the identity structure is not passed in, the ModbusControlBlock
        uses its own empty structure.
        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use, default ModbusRtuFramer
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
        """
        super().__init__(
            CommParams(
                comm_type=CommType.SERIAL,
                comm_name="server_listener",
                reconnect_delay=kwargs.get("reconnect_delay", 2),
                reconnect_delay_max=0.0,
                timeout_connect=kwargs.get("timeout", 3),
                host=kwargs.get("port", 0),
                bytesize=kwargs.get("bytesize", 8),
                parity=kwargs.get("parity", "N"),
                baudrate=kwargs.get("baudrate", 19200),
                stopbits=kwargs.get("stopbits", 1),
            ),
            True,
        )

        self.loop = kwargs.get("loop") or asyncio.get_event_loop()
        self.handle_local_echo = kwargs.get("handle_local_echo", False)
        self.ignore_missing_slaves = kwargs.get("ignore_missing_slaves", False)
        self.broadcast_enable = kwargs.get("broadcast_enable", False)
        self.framer = framer or ModbusRtuFramer
        self.decoder = ServerDecoder()
        self.context = context or ModbusServerContext()
        self.response_manipulator = kwargs.get("response_manipulator", None)
        self.control = ModbusControlBlock()
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)
        self.local_active_connections = {}
        self.request_tracer = None
        self.server = None
        self.control = ModbusControlBlock()
        identity = kwargs.get("identity")
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

    async def start(self):
        """Start connecting."""

    def handle_new_connection(self):
        """Handle incoming connect."""
        return ModbusServerRequestHandler(self)

    def on_connection_lost(self):
        """Call on lost connection."""
        if self.transport is not None:
            self.transport.close()
            self.transport = None

    async def shutdown(self):
        """Terminate server."""
        self.transport_close()
        loop_list = list(self.local_active_connections)
        for k_item in loop_list:
            v_item = self.local_active_connections[k_item]
            Log.warning("aborting active session {}", k_item)
            v_item.transport.close()
            await asyncio.sleep(0.1)
            v_item.handler_task.cancel()
            await v_item.handler_task
        self.local_active_connections = {}
        if self.server:
            self.server.close()
            await asyncio.wait_for(self.server.wait_closed(), 10)
            self.server = None

    async def serve_forever(self):
        """Start endless loop."""
        if self.server:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )
        Log.info("Server(Serial) listening.")
        await self.transport_listen()
        try:
            await self.transport.serve_forever()
        except asyncio.exceptions.CancelledError:
            raise
        except Exception as exc:  # pylint: disable=broad-except
            Log.error("Server unexpected exception {}", exc)


# --------------------------------------------------------------------------- #
# Creation Factories
# --------------------------------------------------------------------------- #


class _serverList:
    """Maintains information about the active server.

    :meta private:
    """

    active_server: Union[ModbusTcpServer, ModbusUdpServer, ModbusSerialServer] = None

    def __init__(self, server):
        """Register new server."""
        self.server = server
        self.loop = asyncio.get_event_loop()

    @classmethod
    async def run(cls, server, custom_functions):
        """Help starting/stopping server."""
        for func in custom_functions:
            server.decoder.register(func)
        cls.active_server = _serverList(server)
        with suppress(asyncio.exceptions.CancelledError):
            await server.serve_forever()

    @classmethod
    async def async_stop(cls):
        """Wait for server stop."""
        if not cls.active_server:
            raise RuntimeError("ServerAsyncStop called without server task active.")
        await cls.active_server.server.shutdown()
        await asyncio.sleep(1)
        cls.active_server = None

    @classmethod
    def stop(cls):
        """Wait for server stop."""
        if not cls.active_server:
            Log.info("ServerStop called without server task active.")
            return
        if not cls.active_server.loop.is_running():
            Log.info("ServerStop called with loop stopped.")
            return
        asyncio.run_coroutine_threadsafe(cls.async_stop(), cls.active_server.loop)
        time.sleep(10)


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
        context, kwargs.pop("framer", ModbusSocketFramer), identity, address, **kwargs
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
        kwargs.pop("framer", ModbusTlsFramer),
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
        context, kwargs.pop("framer", ModbusSocketFramer), identity, address, **kwargs
    )
    await _serverList.run(server, custom_functions)


async def StartAsyncSerialServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    custom_functions=[],
    **kwargs,
):  # pragma: no cover
    """Start and run a serial modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param kwargs: The rest
    """
    server = ModbusSerialServer(
        context, kwargs.pop("framer", ModbusAsciiFramer), identity=identity, **kwargs
    )
    await server.start()
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
