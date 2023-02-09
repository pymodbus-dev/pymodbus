"""Implementation of a Threaded Modbus Server."""
# pylint: disable=missing-type-doc
import asyncio
import ssl
import traceback
from time import sleep

from pymodbus.client.serial_asyncio import create_serial_connection
from pymodbus.constants import Defaults
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock, ModbusDeviceIdentification
from pymodbus.exceptions import NoSuchSlaveException, NotImplementedException
from pymodbus.factory import ServerDecoder
from pymodbus.logging import Log
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


try:
    import serial
except ImportError:
    pass


def sslctx_provider(
    sslctx=None, certfile=None, keyfile=None, password=None, reqclicert=False
):
    """Provide the SSLContext for ModbusTlsServer.

    If the user defined SSLContext is not passed in, sslctx_provider will
    produce a default one.

    :param sslctx: The user defined SSLContext to use for TLS (default None and
                   auto create)
    :param certfile: The cert file path for TLS (used if sslctx is None)
    :param keyfile: The key file path for TLS (used if sslctx is None)
    :param password: The password for for decrypting the private key file
    :param reqclicert: Force the sever request client's certificate
    """
    if sslctx is None:
        # According to MODBUS/TCP Security Protocol Specification, it is
        # TLSv2 at least
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslctx.verify_mode = ssl.CERT_NONE
        sslctx.check_hostname = False
        sslctx.options |= ssl.OP_NO_TLSv1_1
        sslctx.options |= ssl.OP_NO_TLSv1
        sslctx.options |= ssl.OP_NO_SSLv3
        sslctx.options |= ssl.OP_NO_SSLv2
        sslctx.load_cert_chain(certfile=certfile, keyfile=keyfile, password=password)

    if reqclicert:
        sslctx.verify_mode = ssl.CERT_REQUIRED

    return sslctx


# --------------------------------------------------------------------------- #
# Protocol Handlers
# --------------------------------------------------------------------------- #


class ModbusBaseRequestHandler(asyncio.BaseProtocol):
    """Implements modbus slave wire protocol.

    This uses the asyncio.Protocol to implement the client handler.

    When a connection is established, the asyncio.Protocol.connection_made
    callback is called. This callback will setup the connection and
    create and schedule an asyncio.Task and assign it to running_task.

    running_task will be canceled upon connection_lost event.
    """

    def __init__(self, owner):
        """Initialize."""
        self.server = owner
        self.running = False
        self.receive_queue = asyncio.Queue()
        self.handler_task = None  # coroutine to be run on asyncio loop
        self._sent = b""  # for handle_local_echo

    def _log_exception(self):
        """Show log exception."""
        if isinstance(self, ModbusConnectedRequestHandler):
            Log.debug(
                "Handler for stream [{}] has been canceled", self.client_address[:2]
            )
        elif isinstance(self, ModbusSingleRequestHandler):
            Log.debug("Handler for serial port has been cancelled")
        else:
            if hasattr(self, "protocol"):
                sock_name = (
                    self.protocol._sock.getsockname()  # pylint: disable=protected-access
                )
            else:
                sock_name = "No socket"
            Log.debug("Handler for UDP socket [{}] has been canceled", sock_name[1])

    def connection_made(self, transport):
        """Call for socket establish

        For streamed protocols (TCP) this will also correspond to an
        entire conversation; however for datagram protocols (UDP) this
        corresponds to the socket being opened
        """
        try:
            if (
                hasattr(transport, "get_extra_info")
                and transport.get_extra_info("sockname") is not None
            ):
                sockname = transport.get_extra_info("sockname")[:2]
                Log.debug("Socket [{}] opened", sockname)
            elif hasattr(transport, "serial"):
                Log.debug("Serial connection opened on port: {}", transport.serial.port)
            else:
                Log.warning("Unable to get information about transport {}", transport)
            self.transport = transport  # pylint: disable=attribute-defined-outside-init
            self.running = True
            self.framer = (  # pylint: disable=attribute-defined-outside-init
                self.server.framer(
                    self.server.decoder,
                    client=None,
                )
            )

            # schedule the connection handler on the event loop
            self.handler_task = asyncio.create_task(self.handle())
        except Exception as exc:  # pragma: no cover pylint: disable=broad-except
            Log.error(
                "Datastore unable to fulfill request: {}; {}",
                exc,
                traceback.format_exc(),
            )

    def connection_lost(self, call_exc):
        """Call for socket tear down.

        For streamed protocols any break in the network connection will
        be reported here; for datagram protocols, only a teardown of the
        socket itself will result in this call.
        """
        try:
            if self.handler_task:
                self.handler_task.cancel()
            if call_exc is None:
                self._log_exception()
            elif hasattr(self, "client_address"):  # TCP connection
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

    async def handle(self):  # pylint: disable=too-complex
        """Return Asyncio coroutine which represents a single conversation.

        between the modbus slave and master

        Once the client connection is established, the data chunks will be
        fed to this coroutine via the asyncio.Queue object which is fed by
        the ModbusBaseRequestHandler class's callback Future.

        This callback future gets data from either
        asyncio.DatagramProtocol.datagram_received or
        from asyncio.BaseProtocol.data_received.

        This function will execute without blocking in the while-loop and
        yield to the asyncio event loop when the frame is exhausted.
        As a result, multiple clients can be interleaved without any
        interference between them.

        For ModbusConnectedRequestHandler, each connection will be given an
        instance of the handle() coroutine and this instance will be put in the
        active_connections dict. Calling server_close will individually cancel
        each running handle() task.

        For ModbusDisconnectedRequestHandler, a single handle() coroutine will
        be started and maintained. Calling server_close will cancel that task.
        """
        reset_frame = False
        while self.running:
            try:
                units = self.server.context.slaves()
                # this is an asyncio.Queue await, it will never fail
                data = await self._recv_()
                if isinstance(data, tuple):
                    # addr is populated when talking over UDP
                    data, *addr = data
                else:
                    addr = (None,)  # empty tuple

                if not isinstance(units, (list, tuple)):
                    units = [units]
                # if broadcast is enabled make sure to
                # process requests to address 0
                if self.server.broadcast_enable:  # pragma: no cover
                    if 0 not in units:
                        units.append(0)

                Log.debug("Handling data: {}", data, ":hex")

                single = self.server.context.single
                self.framer.processIncomingPacket(
                    data=data,
                    callback=lambda x: self.execute(x, *addr),
                    unit=units,
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
                if isinstance(self, ModbusConnectedRequestHandler):
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
            if self.server.broadcast_enable and not request.unit_id:
                broadcast = True
                # if broadcasting then execute on all slave contexts,
                # note response will be ignored
                for unit_id in self.server.context.slaves():
                    response = request.execute(self.server.context[unit_id])
            else:
                context = self.server.context[request.unit_id]
                response = request.execute(context)
        except NoSuchSlaveException:
            Log.error("requested slave does not exist: {}", request.unit_id)
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
            response.unit_id = request.unit_id
            skip_encoding = False
            if self.server.response_manipulator:
                response, skip_encoding = self.server.response_manipulator(response)
            self.send(response, *addr, skip_encoding=skip_encoding)

    def send(self, message, *addr, **kwargs):
        """Send message."""

        def __send(msg, *addr):
            Log.debug("send: [{}]- {}", message, msg, ":b2a")
            if addr == (None,):
                self._send_(msg)
            else:
                self._send_(msg, *addr)

        if kwargs.get("skip_encoding", False):
            __send(message, *addr)
        elif message.should_respond:
            # self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            __send(pdu, *addr)
        else:
            Log.debug("Skipping sending response!!")

    # ----------------------------------------------------------------------- #
    # Derived class implementations
    # ----------------------------------------------------------------------- #

    def _send_(self, data):  # pragma: no cover
        """Send a request (string) to the network.

        :param data: The unencoded modbus response
        :raises NotImplementedException:
        """
        raise NotImplementedException("Method not implemented by derived class")

    async def _recv_(self):  # pragma: no cover
        """Receive data from the network.

        :raises NotImplementedException:
        """
        raise NotImplementedException("Method not implemented by derived class")


class ModbusConnectedRequestHandler(ModbusBaseRequestHandler, asyncio.Protocol):
    """Implements the modbus server protocol

    This uses asyncio.Protocol to implement
    the client handler for a connected protocol (TCP).
    """

    def connection_made(self, transport):
        """Call when a connection is made."""
        super().connection_made(transport)

        self.client_address = (  # pylint: disable=attribute-defined-outside-init
            transport.get_extra_info("peername")
        )
        self.server.active_connections[self.client_address] = self
        txt = f"TCP client connection established [{self.client_address[:2]}]"
        Log.debug(txt)

    def connection_lost(self, call_exc):
        """Call when the connection is lost or closed."""
        super().connection_lost(call_exc)
        client_addr = self.client_address[:2]
        Log.debug("TCP client disconnected [{}]", client_addr)
        if self.client_address in self.server.active_connections:
            self.server.active_connections.pop(self.client_address)

    def data_received(self, data):
        """Call when some data is received.

        data is a non-empty bytes object containing the incoming data.
        """
        self.receive_queue.put_nowait(data)

    async def _recv_(self):
        try:
            result = await self.receive_queue.get()
        except RuntimeError:
            Log.error("Event loop is closed")
            result = None
        return result

    def _send_(self, data):
        """Send tcp."""
        self.transport.write(data)


class ModbusDisconnectedRequestHandler(
    ModbusBaseRequestHandler, asyncio.DatagramProtocol
):
    """Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler for a disconnected protocol (UDP). The
    only difference is that we have to specify who to send the
    resulting packet data to.
    """

    def __init__(self, owner):
        """Initialize."""
        super().__init__(owner)
        _future = asyncio.get_running_loop().create_future()
        self.server.on_connection_terminated = _future

    def connection_lost(self, call_exc):
        """Handle connection lost."""
        super().connection_lost(call_exc)
        self.server.on_connection_terminated.set_result(True)

    def datagram_received(self, data, addr):
        """Call when a datagram is received.

        data is a bytes object containing the incoming data. addr
        is the address of the peer sending the data; the exact
        format depends on the transport.
        """
        self.receive_queue.put_nowait((data, addr))

    def error_received(self, exc):  # pragma: no cover
        """Call when a previous send/receive raises an OSError.

        exc is the OSError instance.

        This method is called in rare conditions,
        when the transport (e.g. UDP) detects that a datagram could
        not be delivered to its recipient. In many conditions
        though, undeliverable datagrams will be silently dropped.
        """
        Log.error("datagram connection error [{}]", exc)

    async def _recv_(self):
        return await self.receive_queue.get()

    def _send_(self, data, addr=None):
        self.transport.sendto(data, addr=addr)


class ModbusSingleRequestHandler(ModbusBaseRequestHandler, asyncio.Protocol):
    """Implement the modbus server protocol.

    This uses asyncio.Protocol to implement
    the client handler for a serial connection.
    """

    def connection_made(self, transport):
        """Handle connect made."""
        super().connection_made(transport)
        Log.debug("Serial connection established")

    def connection_lost(self, call_exc):
        """Handle connection lost."""
        super().connection_lost(call_exc)
        Log.debug("Serial connection lost")
        if hasattr(self.server, "on_connection_lost"):
            self.server.on_connection_lost()

    def data_received(self, data):
        """Receive data."""
        if (
            hasattr(self.server, "handle_local_echo")
            and self.server.handle_local_echo is True
            and self._sent
        ):
            if self._sent in data:
                data, self._sent = data.replace(self._sent, b"", 1), b""
            elif self._sent.startswith(data):
                self._sent, data = self._sent.replace(data, b"", 1), b""
            else:
                self._sent = b""
            if not data:
                return
        self.receive_queue.put_nowait(data)

    async def _recv_(self):
        return await self.receive_queue.get()

    def _send_(self, data):
        if self.transport is not None:
            self.transport.write(data)
            if (
                hasattr(self.server, "handle_local_echo")
                and self.server.handle_local_echo is True
            ):
                self._sent = data


# --------------------------------------------------------------------------- #
# Server Implementations
# --------------------------------------------------------------------------- #


class ModbusUnixServer:
    """A modbus threaded Unix socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(
        self,
        context,
        path,
        framer=None,
        identity=None,
        handler=None,
        **kwargs,
    ):
        """Initialize the socket server.

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own default structure.

        :param context: The ModbusServerContext datastore
        :param path: unix socket path
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param handler: A handler for each client session; default is
                        ModbusConnectedRequestHandler. The handler class
                        receives connection create/teardown events
        :param allow_reuse_address: Whether the server will allow the
                        reuse of an address.
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                        False to treat 0 as any other unit_id
        :param response_manipulator: Callback method for manipulating the
                                        response
        """
        self.active_connections = {}
        self.loop = kwargs.get("loop") or asyncio.get_event_loop()
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.path = path
        self.handler = handler or ModbusConnectedRequestHandler
        self.handler.server = self
        self.ignore_missing_slaves = kwargs.get(
            "ignore_missing_slaves", Defaults.IgnoreMissingSlaves
        )
        self.broadcast_enable = kwargs.get("broadcast_enable", Defaults.BroadcastEnable)
        self.response_manipulator = kwargs.get("response_manipulator", None)
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        # asyncio future that will be done once server has started
        self.serving = self.loop.create_future()
        # constructors cannot be declared async, so we have to
        # defer the initialization of the server
        self.server = None
        self.request_tracer = None
        self.factory_parms = {}

    async def serve_forever(self):
        """Start endless loop."""
        if self.server is None:
            try:
                self.server = await self.loop.create_unix_server(
                    lambda: self.handler(self),
                    self.path,
                )
                self.serving.set_result(True)
                await self.server.serve_forever()
            except asyncio.exceptions.CancelledError:
                raise
            except Exception as exc:  # pylint: disable=broad-except
                Log.error("Server unexpected exception {}", exc)
        else:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )
        Log.info("Server graceful shutdown.")

    async def shutdown(self):
        """Shutdown server."""
        await self.server_close()

    async def server_close(self):
        """Close server."""
        for k_item, v_item in self.active_connections.items():
            Log.warning("aborting active session {}", k_item)
            v_item.handler_task.cancel()
        self.active_connections = {}
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None


class ModbusTcpServer:
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
        address=None,
        handler=None,
        allow_reuse_address=False,
        defer_start=False,
        backlog=20,
        **kwargs,
    ):
        """Initialize the socket server.

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        :param handler: A handler for each client session; default is
                        ModbusConnectedRequestHandler. The handler class
                        receives connection create/teardown events
        :param allow_reuse_address: Whether the server will allow the
                        reuse of an address.
        :param backlog:  is the maximum number of queued connections
                    passed to listen(). Defaults to 20, increase if many
                    connections are being made and broken to your Modbus slave
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                        False to treat 0 as any other unit_id
        :param response_manipulator: Callback method for manipulating the
                                        response
        """
        self.active_connections = {}
        self.loop = kwargs.get("loop") or asyncio.get_event_loop()
        self.allow_reuse_address = allow_reuse_address
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.address = address or ("", Defaults.TcpPort)
        self.handler = handler or ModbusConnectedRequestHandler
        self.handler.server = self
        self.ignore_missing_slaves = kwargs.get(
            "ignore_missing_slaves", Defaults.IgnoreMissingSlaves
        )
        self.broadcast_enable = kwargs.get("broadcast_enable", Defaults.BroadcastEnable)
        self.response_manipulator = kwargs.get("response_manipulator", None)
        self.request_tracer = kwargs.get("request_tracer", None)
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        # asyncio future that will be done once server has started
        self.serving = self.loop.create_future()
        # constructors cannot be declared async, so we have to
        # defer the initialization of the server
        self.server = None
        self.factory_parms = {
            "reuse_address": allow_reuse_address,
            "backlog": backlog,
            "start_serving": not defer_start,
        }

    async def serve_forever(self):
        """Start endless loop."""
        if self.server is None:
            self.server = await self.loop.create_server(
                lambda: self.handler(self),
                *self.address,
                **self.factory_parms,
            )
            self.serving.set_result(True)
            try:
                await self.server.serve_forever()
            except asyncio.exceptions.CancelledError:
                raise
            except Exception as exc:  # pylint: disable=broad-except
                Log.error("Server unexpected exception {}", exc)
        else:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )
        Log.info("Server graceful shutdown.")

    async def shutdown(self):
        """Shutdown server."""
        await self.server_close()

    async def server_close(self):
        """Close server."""
        for k_item, v_item in self.active_connections.items():
            Log.warning("aborting active session {}", k_item)
            v_item.handler_task.cancel()
        self.active_connections = {}
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None


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
        address=None,
        sslctx=None,
        certfile=None,
        keyfile=None,
        password=None,
        reqclicert=False,
        handler=None,
        allow_reuse_address=False,
        defer_start=False,
        backlog=20,
        **kwargs,
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
        :param reqclicert: Force the sever request client's certificate
        :param handler: A handler for each client session; default is
                        ModbusConnectedRequestHandler. The handler class
                        receives connection create/teardown events
        :param allow_reuse_address: Whether the server will allow the
                        reuse of an address.
        :param backlog:  is the maximum number of queued connections
                    passed to listen(). Defaults to 20, increase if many
                    connections are being made and broken to your Modbus slave
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                        False to treat 0 as any other unit_id
        :param response_manipulator: Callback method for
                        manipulating the response
        """
        super().__init__(
            context,
            framer=framer,
            identity=identity,
            address=address,
            handler=handler,
            allow_reuse_address=allow_reuse_address,
            defer_start=defer_start,
            backlog=backlog,
            **kwargs,
        )
        self.sslctx = sslctx_provider(sslctx, certfile, keyfile, password, reqclicert)
        self.factory_parms["ssl"] = self.sslctx


class ModbusUdpServer:
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
        address=None,
        handler=None,
        defer_start=False,  # pylint: disable=unused-argument
        backlog=20,  # pylint: disable=unused-argument
        **kwargs,
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
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                            False to treat 0 as any other unit_id
        :param response_manipulator: Callback method for
                            manipulating the response
        """
        self.loop = asyncio.get_running_loop()
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.address = address or ("", Defaults.TcpPort)
        self.handler = handler or ModbusDisconnectedRequestHandler
        self.ignore_missing_slaves = kwargs.get(
            "ignore_missing_slaves", Defaults.IgnoreMissingSlaves
        )
        self.broadcast_enable = kwargs.get("broadcast_enable", Defaults.BroadcastEnable)
        self.response_manipulator = kwargs.get("response_manipulator", None)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        self.protocol = None
        self.endpoint = None
        self.on_connection_terminated = None
        # asyncio future that will be done once server has started
        self.serving = self.loop.create_future()
        self.factory_parms = {
            "local_addr": self.address,
            "allow_broadcast": True,
        }
        self.request_tracer = None

    async def serve_forever(self):
        """Start endless loop."""
        if self.protocol is None:
            try:
                self.protocol, self.endpoint = await self.loop.create_datagram_endpoint(
                    lambda: self.handler(self),
                    **self.factory_parms,
                )
            except asyncio.exceptions.CancelledError:
                raise
            except Exception as exc:
                Log.error("Server unexpected exception {}", exc)
                raise RuntimeError(exc) from exc
            self.serving.set_result(True)
        else:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )

    async def shutdown(self):
        """Shutdown server."""
        await self.server_close()

    async def server_close(self):
        """Close server."""
        if self.endpoint:
            self.endpoint.running = False
        if self.endpoint is not None and self.endpoint.handler_task is not None:
            self.endpoint.handler_task.cancel()
        if self.protocol is not None:
            self.protocol.close()
            self.protocol = None


class ModbusSerialServer:  # pylint: disable=too-many-instance-attributes
    """A modbus threaded serial socket server.

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    handler = None

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
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                            False to treat 0 as any other unit_id
        :param auto_reconnect: True to enable automatic reconnection,
                            False otherwise
        :param reconnect_delay: reconnect delay in seconds
        :param response_manipulator: Callback method for
                    manipulating the response
        """
        self.loop = kwargs.get("loop") or asyncio.get_event_loop()
        self.bytesize = kwargs.get("bytesize", Defaults.Bytesize)
        self.parity = kwargs.get("parity", Defaults.Parity)
        self.baudrate = kwargs.get("baudrate", Defaults.Baudrate)
        self.timeout = kwargs.get("timeout", Defaults.Timeout)
        self.device = kwargs.get("port", 0)
        self.stopbits = kwargs.get("stopbits", Defaults.Stopbits)
        self.handle_local_echo = kwargs.get(
            "handle_local_echo", Defaults.HandleLocalEcho
        )
        self.ignore_missing_slaves = kwargs.get(
            "ignore_missing_slaves", Defaults.IgnoreMissingSlaves
        )
        self.broadcast_enable = kwargs.get("broadcast_enable", Defaults.BroadcastEnable)
        self.auto_reconnect = kwargs.get("auto_reconnect", False)
        self.reconnect_delay = kwargs.get("reconnect_delay", 2)
        self.reconnecting_task = None
        self.handler = kwargs.get("handler") or ModbusSingleRequestHandler
        self.framer = framer or ModbusRtuFramer
        self.decoder = ServerDecoder()
        self.context = context or ModbusServerContext()
        self.response_manipulator = kwargs.get("response_manipulator", None)
        self.control = ModbusControlBlock()
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        self.request_tracer = None
        self.protocol = None
        self.transport = None
        self.server = None
        self.control = ModbusControlBlock()
        identity = kwargs.get("identity")
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

    async def start(self):
        """Start connecting."""
        await self._connect()

    async def _delayed_connect(self):
        """Delay connect."""
        await asyncio.sleep(self.reconnect_delay)
        await self._connect()

    async def _connect(self):
        """Connect."""
        if self.reconnecting_task is not None:
            self.reconnecting_task = None
        if self.device.startswith("socket:"):
            return
        try:
            self.transport, self.protocol = await create_serial_connection(
                self.loop,
                lambda: self.handler(self),
                self.device,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout,
            )
        except serial.serialutil.SerialException as exc:
            Log.debug("Failed to open serial port: {}", self.device)
            if not self.auto_reconnect:
                raise exc
            self._check_reconnect()
        except Exception as exc:  # pylint: disable=broad-except
            Log.debug("Exception while create - {}", exc)

    def on_connection_lost(self):
        """Call on lost connection."""
        if self.transport is not None:
            self.transport.close()
            self.transport = None
            self.protocol = None
        if self.server is None:
            self._check_reconnect()

    async def shutdown(self):
        """Terminate server."""
        if self.transport is not None:
            self.transport.abort()
        if self.server is not None:
            self.server.close()
            await asyncio.wait_for(self.server.wait_closed(), 10)
        self.server = None
        self.transport = None
        self.protocol = None

    def _check_reconnect(self):
        """Check reconnect."""
        Log.debug(
            "checking autoreconnect {} {}", self.auto_reconnect, self.reconnecting_task
        )
        if self.auto_reconnect and (self.reconnecting_task is None):
            Log.debug("Scheduling serial connection reconnect")
            self.reconnecting_task = self.loop.create_task(self._delayed_connect())

    async def serve_forever(self):
        """Start endless loop."""
        if self.server:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )
        if self.device.startswith("socket:"):
            # Socket server means listen so start a socket server
            parts = self.device[9:].split(":")
            host_addr = (parts[0], int(parts[1]))
            self.server = await self.loop.create_server(
                lambda: self.handler(self),
                *host_addr,
                reuse_address=True,
                start_serving=True,
                backlog=20,
            )
            try:
                await self.server.serve_forever()
            except asyncio.exceptions.CancelledError:
                raise
            except Exception as exc:  # pylint: disable=broad-except
                Log.error("Server unexpected exception {}", exc)
            return

        while self.server or self.transport or self.protocol:
            await asyncio.sleep(10)


# --------------------------------------------------------------------------- #
# Creation Factories
# --------------------------------------------------------------------------- #


class _serverList:
    """Maintains a list of active servers.

    The list allows applications to have multiple servers and
    being able to do shutdown gracefully.
    """

    _servers = []

    def __init__(self, server, custom_functions, register):
        """Register new server."""
        for func in custom_functions:
            server.decoder.register(func)
        self.server = server
        if register:
            self._servers.append(self)
        self.job_stop = asyncio.Event()
        self.job_is_stopped = asyncio.Event()
        self.task = None
        self.loop = asyncio.get_event_loop()

    @classmethod
    def get_server(cls):
        """Get server at index."""
        return cls._servers[-1] if cls._servers else None

    def _remove(self):
        """Remove server from active list."""
        server = self._servers[-1]
        self._servers.pop()
        del server

    async def _run(self):
        """Help starting/stopping server."""
        # self.task = asyncio.create_task(self.server.serve_forever())
        # await self.job_stop.wait()
        # await self.server.shutdown()
        # await asyncio.sleep(0.1)
        # self.task.cancel()
        # await asyncio.sleep(0.1)
        # try:
        #     await asyncio.wait_for(self.task, 10)
        # except asyncio.CancelledError:
        #     pass
        # self.job_is_stopped.set()

    async def run(self):
        """Help starting/stopping server."""
        try:
            # await self._run()
            await self.server.serve_forever()
        except asyncio.CancelledError:
            pass

    async def async_await_stop(self):
        """Wait for server stop."""
        await self.server.shutdown()
        # self.job_stop.set()
        # try:
        #    await asyncio.wait_for(self.job_is_stopped.wait(), 60)
        # except asyncio.exceptions.CancelledError:
        #    pass
        # self._remove()


async def StartAsyncUnixServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    path=None,
    custom_functions=[],
    defer_start=False,
    **kwargs,
):
    """Start and run a tcp modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param path: An optional path to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param defer_start: if set, the server object will be returned ready to start.
            Otherwise, the server will be immediately spun
            up without the ability to shut it off
    :param kwargs: The rest
    :return: an initialized but inactive server object coroutine
    """
    server = ModbusUnixServer(
        context, path, kwargs.pop("framer", ModbusSocketFramer), identity, **kwargs
    )
    if not defer_start:
        job = _serverList(server, custom_functions, not defer_start)
        await job.run()
    return server


async def StartAsyncTcpServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    address=None,
    custom_functions=[],
    defer_start=False,
    **kwargs,
):
    """Start and run a tcp modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param defer_start: if set, the server object will be returned ready to start.
            Otherwise, the server will be immediately spun
            up without the ability to shut it off
    :param kwargs: The rest
    :return: an initialized but inactive server object coroutine
    """
    server = ModbusTcpServer(
        context, kwargs.pop("framer", ModbusSocketFramer), identity, address, **kwargs
    )
    if not defer_start:
        job = _serverList(server, custom_functions, not defer_start)
        await job.run()
    return server


async def StartAsyncTlsServer(  # pylint: disable=invalid-name,dangerous-default-value,too-many-arguments
    context=None,
    identity=None,
    address=None,
    sslctx=None,
    certfile=None,
    keyfile=None,
    password=None,
    reqclicert=False,
    allow_reuse_address=False,
    custom_functions=[],
    defer_start=False,
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
    :param reqclicert: Force the sever request client's certificate
    :param allow_reuse_address: Whether the server will allow the reuse of an
                                address.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param defer_start: if set, the server object will be returned ready to start.
            Otherwise, the server will be immediately spun
            up without the ability to shut it off
    :param kwargs: The rest
    :return: an initialized but inactive server object coroutine
    """
    server = ModbusTlsServer(
        context,
        kwargs.pop("framer", ModbusTlsFramer),
        identity,
        address,
        sslctx,
        certfile,
        keyfile,
        password,
        reqclicert,
        allow_reuse_address=allow_reuse_address,
        **kwargs,
    )
    if not defer_start:
        job = _serverList(server, custom_functions, not defer_start)
        await job.run()
    return server


async def StartAsyncUdpServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    address=None,
    custom_functions=[],
    defer_start=False,
    **kwargs,
):
    """Start and run a udp modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param defer_start: if set, the server object will be returned ready to start.
            Otherwise, the server will be immediately spun
            up without the ability to shut it off
    :param kwargs:
    """
    server = ModbusUdpServer(
        context, kwargs.pop("framer", ModbusSocketFramer), identity, address, **kwargs
    )
    if not defer_start:
        job = _serverList(server, custom_functions, not defer_start)
        await job.run()
    return server


async def StartAsyncSerialServer(  # pylint: disable=invalid-name,dangerous-default-value
    context=None,
    identity=None,
    custom_functions=[],
    defer_start=False,
    **kwargs,
):  # pragma: no cover
    """Start and run a serial modbus server.

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param defer_start: if set, the server object will be returned ready to start.
            Otherwise, the server will be immediately spun
            up without the ability to shut it off
    :param kwargs: The rest
    """
    server = ModbusSerialServer(
        context, kwargs.pop("framer", ModbusAsciiFramer), identity=identity, **kwargs
    )
    if not defer_start:
        job = _serverList(server, custom_functions, not defer_start)
        await server.start()
        await job.run()
    return server


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
    if my_job := _serverList.get_server():
        await my_job.async_await_stop()
        await asyncio.sleep(0.1)
    else:
        raise RuntimeError("ServerAsyncStop called without server task active.")


def ServerStop():  # pylint: disable=invalid-name
    """Terminate server."""
    if my_job := _serverList.get_server():
        if my_job.loop.is_running():
            asyncio.run_coroutine_threadsafe(my_job.async_await_stop(), my_job.loop)
            sleep(0.1)
    else:
        raise RuntimeError("ServerStop called without server task active.")
