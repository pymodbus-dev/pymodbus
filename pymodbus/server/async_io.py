"""Implementation of a Threaded Modbus Server."""
# pylint: disable=missing-type-doc
import asyncio
import logging
import platform
import ssl
import traceback
from binascii import b2a_hex
from time import sleep

from pymodbus.constants import Defaults
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock, ModbusDeviceIdentification
from pymodbus.exceptions import NoSuchSlaveException, NotImplementedException
from pymodbus.factory import ServerDecoder
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)
from pymodbus.utilities import hexlify_packets


try:
    import serial
    from serial_asyncio import create_serial_connection
except ImportError:
    pass


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)


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
    :param reqclicert: Force the sever request client"s certificate
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

    def _log_exception(self):
        """Show log exception."""
        if isinstance(self, ModbusConnectedRequestHandler):
            txt = f"Handler for stream [{self.client_address[:2]}] has been canceled"
            _logger.debug(txt)
        elif isinstance(self, ModbusSingleRequestHandler):
            _logger.debug("Handler for serial port has been cancelled")
        else:
            if hasattr(self, "protocol"):
                sock_name = (
                    self.protocol._sock.getsockname()  # pylint: disable=protected-access
                )
            else:
                sock_name = "No socket"
            txt = f"Handler for UDP socket [{sock_name[1]}] has been canceled"
            _logger.debug(txt)

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
                txt = f"Socket [{sockname}] opened"
                _logger.debug(txt)
            elif hasattr(transport, "serial"):
                txt = f"Serial connection opened on port: {transport.serial.port}"
                _logger.debug(txt)
            else:
                txt = f"Unable to get information about transport {transport}"
                _logger.warning(txt)
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
            txt = (
                f"Datastore unable to fulfill request: {exc}; {traceback.format_exc()}"
            )
            _logger.error(txt)

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
                txt = f"Client Disconnection {self.client_address} due to {call_exc}"
                _logger.debug(txt)

            self.running = False
        except Exception as exc:  # pylint: disable=broad-except
            txt = (
                f"Datastore unable to fulfill request: {exc}; {traceback.format_exc()}"
            )
            _logger.error(txt)

    async def handle(self):  # pylint: disable=too-complex
        """Return Asyncio coroutine which represents a single conversation.

        between the modbus slave and master

        Once the client connection is established, the data chunks will be
        fed to this coroutine via the asyncio.Queue object which is fed by
        the ModbusBaseRequestHandler class"s callback Future.

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

                if _logger.isEnabledFor(logging.DEBUG):
                    txt = f"Handling data: {hexlify_packets(data)}"
                    _logger.debug(txt)

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
                    txt = f'Unknown exception "{exc}" on stream {client_addr} forcing disconnect'
                    _logger.error(txt)
                    self.transport.close()
                else:
                    txt = f"Unknown error occurred {exc}"
                    _logger.error(exc)
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
            txt = f"requested slave does not exist: {request.unit_id}"
            _logger.error(txt)
            if self.server.ignore_missing_slaves:
                return  # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as exc:  # pylint: disable=broad-except
            txt = (
                f"Datastore unable to fulfill request: {exc}; {traceback.format_exc()}"
            )
            _logger.error(txt)
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
            if _logger.isEnabledFor(logging.DEBUG):
                txt = f"send: [{message}]- {b2a_hex(msg)}"
                _logger.debug(txt)
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
            _logger.debug("Skipping sending response!!")

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
        _logger.debug(txt)

    def connection_lost(self, call_exc):
        """Call when the connection is lost or closed."""
        super().connection_lost(call_exc)
        client_addr = self.client_address[:2]
        txt = f"TCP client disconnected [{client_addr}]"
        _logger.debug(txt)
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
            _logger.error("Event loop is closed")
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
        txt = f"datagram connection error [{exc}]"
        _logger.error(txt)

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
        _logger.debug("Serial connection established")

    def connection_lost(self, call_exc):
        """Handle connection lost."""
        super().connection_lost(call_exc)
        _logger.debug("Serial connection lost")
        if hasattr(self.server, "on_connection_lost"):
            self.server.on_connection_lost()

    def data_received(self, data):
        """Receive data."""
        self.receive_queue.put_nowait(data)

    async def _recv_(self):
        return await self.receive_queue.get()

    def _send_(self, data):
        if self.transport is not None:
            self.transport.write(data)


# --------------------------------------------------------------------------- #
# Server Implementations
# --------------------------------------------------------------------------- #


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
        allow_reuse_port=False,
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
        :param allow_reuse_port: Whether the server will allow the
                        reuse of a port.
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
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        # asyncio future that will be done once server has started
        self.serving = self.loop.create_future()
        # constructors cannot be declared async, so we have to
        # defer the initialization of the server
        self.server = None
        self.factory_parms = {
            "reuse_address": allow_reuse_address,
            "reuse_port": allow_reuse_port,
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
                txt = f"Server unexpected exception {exc}"
                _logger.error(txt)
        else:
            raise RuntimeError(
                "Can't call serve_forever on an already running server object"
            )
        _logger.info("Server graceful shutdown.")

    async def shutdown(self):
        """Shutdown server."""
        await self.server_close()

    async def server_close(self):
        """Close server."""
        for k_item, v_item in self.active_connections.items():
            txt = f"aborting active session {k_item}"
            _logger.warning(txt)
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
        allow_reuse_port=False,
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
        :param reqclicert: Force the sever request client"s certificate
        :param handler: A handler for each client session; default is
                        ModbusConnectedRequestHandler. The handler class
                        receives connection create/teardown events
        :param allow_reuse_address: Whether the server will allow the
                        reuse of an address.
        :param allow_reuse_port: Whether the server will allow the
                        reuse of a port.
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
            allow_reuse_port=allow_reuse_port,
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
        allow_reuse_address=False,
        allow_reuse_port=False,
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
        self.stop_serving = self.loop.create_future()
        # asyncio future that will be done once server has started
        self.serving = self.loop.create_future()
        self.factory_parms = {
            "local_addr": self.address,
            "reuse_address": allow_reuse_address,
            "reuse_port": allow_reuse_port,
            "allow_broadcast": True,
        }

    async def serve_forever(self):
        """Start endless loop."""
        if self.protocol is None:
            try:
                self.protocol, self.endpoint = await self.loop.create_datagram_endpoint(
                    lambda: self.handler(self),
                    **self.factory_parms,
                )
            except asyncio.exceptions.CancelledError:
                pass
            self.serving.set_result(True)
            await self.stop_serving
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
        if not self.stop_serving.done():
            self.stop_serving.set_result(True)
        if self.endpoint is not None and self.endpoint.handler_task is not None:
            self.endpoint.handler_task.cancel()
        if self.protocol is not None:
            self.protocol.close()
            # TBD await self.protocol.wait_closed()
            self.protocol = None


class ModbusSerialServer:
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
        self.bytesize = kwargs.get("bytesize", Defaults.Bytesize)
        self.parity = kwargs.get("parity", Defaults.Parity)
        self.baudrate = kwargs.get("baudrate", Defaults.Baudrate)
        self.timeout = kwargs.get("timeout", Defaults.Timeout)
        self.device = kwargs.get("port", 0)
        self.stopbits = kwargs.get("stopbits", Defaults.Stopbits)
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
                asyncio.get_event_loop(),
                lambda: self.handler(self),
                self.device,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=self.timeout,
            )
        except serial.serialutil.SerialException as exc:
            txt = f"Failed to open serial port: {self.device}"
            _logger.debug(txt)
            if not self.auto_reconnect:
                raise exc
            self._check_reconnect()
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Exception while create - {exc}"
            _logger.debug(txt)

    def on_connection_lost(self):
        """Call on lost connection."""
        if self.transport is not None:
            self.transport.close()
            self.transport = None
            self.protocol = None

        self._check_reconnect()

    async def shutdown(self):
        """Terminate server."""
        if self.transport is not None:
            self.transport.close()
            self.transport = None
            self.protocol = None

    def _check_reconnect(self):
        """Check reconnect."""
        txt = f"checking autoreconnect {self.auto_reconnect} {self.reconnecting_task}"
        _logger.debug(txt)
        if self.auto_reconnect and (self.reconnecting_task is None):
            _logger.debug("Scheduling serial connection reconnect")
            loop = asyncio.get_event_loop()
            self.reconnecting_task = loop.create_task(self._delayed_connect())

    async def serve_forever(self):
        """Start endless loop."""
        if self.device.startswith("socket:"):
            # Socket server means listen so start a socket server
            parts = self.device[7:].split(":")
            host_port = ("", int(parts[1]))
            self.server = await asyncio.get_event_loop().create_server(
                lambda: self.handler(self),
                *host_port,
                reuse_address=True,
                reuse_port=True,
                start_serving=True,
                backlog=20,
            )
            await self.server.serve_forever()
            return

        while True:
            await asyncio.sleep(360)


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

    @classmethod
    def get_server(cls):
        """Get server at index."""
        return cls._servers[-1]

    def _remove(self):
        """Remove server from active list."""
        server = self._servers[-1]
        self._servers.pop()
        del server

    async def run(self):
        """Help starting/stopping server."""
        try:
            self.task = asyncio.create_task(self.server.serve_forever())
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Server caught exception: {exc}"
            _logger.error(txt)
        await self.job_stop.wait()
        await self.server.shutdown()
        await asyncio.sleep(0.1)
        self.task.cancel()
        await asyncio.sleep(0.1)
        try:
            await asyncio.wait_for(self.task, 10)
        except asyncio.CancelledError:
            pass
        if platform.system().lower() == "windows":
            owntask = asyncio.current_task()
            for task in asyncio.all_tasks():
                if task != owntask:
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, 10)
                    except asyncio.CancelledError:
                        pass
        self.job_is_stopped.set()

    def request_stop(self):
        """Request server stop."""
        self.job_stop.set()

    async def async_await_stop(self):
        """Wait for server stop."""
        try:
            await self.job_is_stopped.wait()
        except asyncio.exceptions.CancelledError:
            pass
        self._remove()

    def await_stop(self):
        """Wait for server stop."""
        for i in range(30):  # Loop for 3 seconds
            sleep(0.1)  # in steps of 100 milliseconds.
            if self.job_is_stopped.is_set():
                break
        self._remove()


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
    job = _serverList(server, custom_functions, not defer_start)
    if defer_start:
        return server
    await job.run()


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
    allow_reuse_port=False,
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
    :param reqclicert: Force the sever request client"s certificate
    :param allow_reuse_address: Whether the server will allow the reuse of an
                                address.
    :param allow_reuse_port: Whether the server will allow the reuse of a port.
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
        allow_reuse_port=allow_reuse_port,
        **kwargs,
    )
    job = _serverList(server, custom_functions, not defer_start)
    if defer_start:
        return server
    await job.run()


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
    job = _serverList(server, custom_functions, not defer_start)
    if defer_start:
        return server
    await job.run()


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
    job = _serverList(server, custom_functions, not defer_start)
    if defer_start:
        return server
    await server.start()
    await job.run()


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
    my_job = _serverList.get_server()
    my_job.request_stop()
    await my_job.async_await_stop()


def ServerStop():  # pylint: disable=invalid-name
    """Terminate server."""
    my_job = _serverList.get_server()
    my_job.request_stop()
    my_job.await_stop()
