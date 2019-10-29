"""
Implementation of a Threaded Modbus Server
------------------------------------------

"""
from binascii import b2a_hex
import socket
import traceback

import asyncio
from pymodbus.compat import PYTHON_VERSION
from pymodbus.constants import Defaults
from pymodbus.utilities import hexlify_packets
from pymodbus.factory import ServerDecoder
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import *
from pymodbus.exceptions import NotImplementedException, NoSuchSlaveException
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.compat import socketserver, byte2int

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Protocol Handlers
# --------------------------------------------------------------------------- #

class ModbusBaseRequestHandler(asyncio.BaseProtocol):
    """ Implements modbus slave wire protocol
    This uses the asyncio.Protocol to implement the client handler.

    When a connection is established, the asyncio.Protocol.connection_made
    callback is called. This callback will setup the connection and
    create and schedule an asyncio.Task and assign it to running_task.

    running_task will be canceled upon connection_lost event.
    """
    def __init__(self, owner):
        self.server = owner
        self.running = False
        self.receive_queue = asyncio.Queue()
        self.handler_task = None # coroutine to be run on asyncio loop

    def connection_made(self, transport):
        """
        asyncio.BaseProtocol callback for socket establish

        For streamed protocols (TCP) this will also correspond to an
        entire conversation; however for datagram protocols (UDP) this
        corresponds to the socket being opened
        """
        try:
            _logger.debug("Socket [%s:%s] opened" % transport.get_extra_info('sockname'))
            self.transport = transport
            self.running = True
            self.framer = self.server.framer(self.server.decoder, client=None)

            # schedule the connection handler on the event loop
            if PYTHON_VERSION >= (3, 7):
                self.handler_task = asyncio.create_task(self.handle())
            else:
                self.handler_task = asyncio.ensure_future(self.handle())
        except Exception as ex: # pragma: no cover
            _logger.debug("Datastore unable to fulfill request: "
                          "%s; %s", ex, traceback.format_exc())

    def connection_lost(self, exc):
        """
        asyncio.BaseProtocol callback for socket tear down

        For streamed protocols any break in the network connection will
        be reported here; for datagram protocols, only a teardown of the
        socket itself will result in this call.
        """
        try:
            self.handler_task.cancel()

            if exc is None:
                if hasattr(self, "client_address"): # TCP connection
                    _logger.debug("Disconnected from client [%s:%s]" % self.client_address)
                else:
                    _logger.debug("Disconnected from client [%s]" % self.transport.get_extra_info("peername"))
            else:  # pragma: no cover
                __logger.debug("Client Disconnection [%s:%s] due to %s" % (*self.client_address, exc))

            self.running = False

        except Exception as ex: # pragma: no cover
            _logger.debug("Datastore unable to fulfill request: "
                      "%s; %s", ex, traceback.format_exc())

    async def handle(self):
        """Asyncio coroutine which represents a single conversation between
        the modbus slave and master

        Once the client connection is established, the data chunks will be
        fed to this coroutine via the asyncio.Queue object which is fed by
        the ModbusBaseRequestHandler class's callback Future.

        This callback future gets data from either asyncio.DatagramProtocol.datagram_received
        or from asyncio.BaseProtocol.data_received.

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
                data = await self._recv_() # this is an asyncio.Queue await, it will never fail
                if isinstance(data, tuple):
                    data, *addr = data # addr is populated when talking over UDP
                else:
                    addr = (None,) # empty tuple

                if not isinstance(units, (list, tuple)):
                    units = [units]
                # if broadcast is enabled make sure to
                # process requests to address 0
                if self.server.broadcast_enable: # pragma: no cover
                    if 0 not in units:
                        units.append(0)

                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug('Handling data: ' + hexlify_packets(data))

                single = self.server.context.single
                self.framer.processIncomingPacket(data=data,
                                                  callback=lambda x: self.execute(x, *addr),
                                                  unit=units,
                                                  single=single)

            except asyncio.CancelledError:
                # catch and ignore cancelation errors
                if isinstance(self, ModbusConnectedRequestHandler):
                    _logger.debug("Handler for stream [%s:%s] has been canceled" % self.client_address)
                else:
                    _logger.debug("Handler for UDP socket [%s] has been canceled" % self.protocol._sock.getsockname()[1])

            except Exception as e:
                # force TCP socket termination as processIncomingPacket should handle applicaiton layer errors
                # for UDP sockets, simply reset the frame
                if isinstance(self, ModbusConnectedRequestHandler):
                    _logger.info("Unknown exception '%s' on stream [%s:%s] forcing disconnect" % (e, *self.client_address))
                    self.transport.close()
                else:
                    _logger.error("Unknown error occurred %s" % e)
                    reset_frame = True  # graceful recovery
            finally:
                if reset_frame:
                    self.framer.resetFrame()
                    reset_frame = False

    def execute(self, request, *addr):
        """ The callback to call with the resulting message

        :param request: The decoded request message
        """
        broadcast = False
        try:
            if self.server.broadcast_enable and request.unit_id == 0:
                broadcast = True
                # if broadcasting then execute on all slave contexts, note response will be ignored
                for unit_id in self.server.context.slaves():
                    response = request.execute(self.server.context[unit_id])
            else:
                context = self.server.context[request.unit_id]
                response = request.execute(context)
        except NoSuchSlaveException as ex:
            _logger.debug("requested slave does "
                          "not exist: %s" % request.unit_id )
            if self.server.ignore_missing_slaves:
                return  # the client will simply timeout waiting for a response
            response = request.doException(merror.GatewayNoResponse)
        except Exception as ex:
            _logger.debug("Datastore unable to fulfill request: "
                          "%s; %s", ex, traceback.format_exc())
            response = request.doException(merror.SlaveFailure)
        # no response when broadcasting
        if not broadcast:
            response.transaction_id = request.transaction_id
            response.unit_id = request.unit_id
            self.send(response, *addr)


    def send(self, message, *addr):
        if message.should_respond:
            # self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: [%s]- %s' % (message, b2a_hex(pdu)))
            if addr == (None,):
                self._send_(pdu)
            else:
                self._send_(pdu, *addr)

    # ----------------------------------------------------------------------- #
    # Derived class implementations
    # ----------------------------------------------------------------------- #

    def _send_(self, data): # pragma: no cover
        """ Send a request (string) to the network

        :param message: The unencoded modbus response
        """
        raise NotImplementedException("Method not implemented "
                                      "by derived class")
    async def _recv_(self): # pragma: no cover
        """ Receive data from the network

        :return:
        """
        raise NotImplementedException("Method not implemented "
                                      "by derived class")


class ModbusConnectedRequestHandler(ModbusBaseRequestHandler,asyncio.Protocol):
    """ Implements the modbus server protocol

    This uses asyncio.Protocol to implement
    the client handler for a connected protocol (TCP).
    """

    def connection_made(self, transport):
        """ asyncio.BaseProtocol:  Called when a connection is made. """
        super().connection_made(transport)

        self.client_address = transport.get_extra_info('peername')
        self.server.active_connections[self.client_address] = self
        _logger.debug("TCP client connection established [%s:%s]" % self.client_address)

    def connection_lost(self, exc):
        """ asyncio.BaseProtocol: Called when the connection is lost or closed."""
        super().connection_lost(exc)
        _logger.debug("TCP client disconnected [%s:%s]" % self.client_address)
        if self.client_address in self.server.active_connections:
            self.server.active_connections.pop(self.client_address)


    def data_received(self,data):
        """
        asyncio.Protocol: (TCP) Called when some data is received.
        data is a non-empty bytes object containing the incoming data.
        """
        self.receive_queue.put_nowait(data)

    async def _recv_(self):
        return await self.receive_queue.get()

    def _send_(self, data):
        """ tcp send """
        self.transport.write(data)


class ModbusDisconnectedRequestHandler(ModbusBaseRequestHandler, asyncio.DatagramProtocol):
    """ Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler for a disconnected protocol (UDP). The
    only difference is that we have to specify who to send the
    resulting packet data to.
    """
    def __init__(self,owner):
        super().__init__(owner)
        self.server.on_connection_terminated = asyncio.get_event_loop().create_future()

    def connection_lost(self,exc):
        super().connection_lost(exc)
        self.server.on_connection_terminated.set_result(True)

    def datagram_received(self,data, addr):
        """
        asyncio.DatagramProtocol: Called when a datagram is received.
         data is a bytes object containing the incoming data. addr
         is the address of the peer sending the data; the exact
         format depends on the transport.
        """
        self.receive_queue.put_nowait((data, addr))

    def error_received(self,exc): # pragma: no cover
        """
        asyncio.DatagramProtocol: Called when a previous send
        or receive operation raises an OSError. exc is the
        OSError instance.

        This method is called in rare conditions,
        when the transport (e.g. UDP) detects that a datagram could
        not be delivered to its recipient. In many conditions
        though, undeliverable datagrams will be silently dropped.
        """
        _logger.error("datagram connection error [%s]" % exc)

    async def _recv_(self):
        return await self.receive_queue.get()

    def _send_(self, data, addr):
        self.transport.sendto(data, addr=addr)

class ModbusServerFactory:
    """
    Builder class for a modbus server

    This also holds the server datastore so that it is persisted between connections
    """

    def __init__(self, store, framer=None, identity=None, **kwargs):
        import warnings
        warnings.warn("deprecated API for asyncio. ServerFactory's are a twisted construct and don't have an equivalent in asyncio",
                      DeprecationWarning)


# --------------------------------------------------------------------------- #
# Server Implementations
# --------------------------------------------------------------------------- #
class ModbusTcpServer:
    """
    A modbus threaded tcp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(self,
                 context,
                 framer=None,
                 identity=None,
                 address=None,
                 handler=None,
                 allow_reuse_address=False,
                 allow_reuse_port=False,
                 defer_start=False,
                 backlog=20,
                 loop=None,
                 **kwargs):
        """ Overloaded initializer for the socket server

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
        :param loop: optional asyncio event loop to run in. Will default to
                        asyncio.get_event_loop() supplied value if None.
        :param ignore_missing_slaves: True to not send errors on a request
                        to a missing slave
        :param broadcast_enable: True to treat unit_id 0 as broadcast address,
                        False to treat 0 as any other unit_id
        """
        self.active_connections = {}
        self.loop = loop or asyncio.get_event_loop()
        self.allow_reuse_address = allow_reuse_address
        self.decoder = ServerDecoder()
        self.framer = framer or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.address = address or ("", Defaults.Port)
        self.handler = handler or ModbusConnectedRequestHandler
        self.handler.server = self
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves',
                                                Defaults.IgnoreMissingSlaves)
        self.broadcast_enable = kwargs.get('broadcast_enable',
                                           Defaults.broadcast_enable)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        self.serving = self.loop.create_future()  # asyncio future that will be done once server has started
        self.server = None # constructors cannot be declared async, so we have to defer the initialization of the server
        if PYTHON_VERSION >= (3, 7):
            # start_serving is new in version 3.7
            self.server_factory = self.loop.create_server(lambda : self.handler(self),
                                                   *self.address,
                                                   reuse_address=allow_reuse_address,
                                                   reuse_port=allow_reuse_port,
                                                   backlog=backlog,
                                                   start_serving=not defer_start)
        else:
            self.server_factory = self.loop.create_server(lambda : self.handler(self),
                                                   *self.address,
                                                   reuse_address=allow_reuse_address,
                                                   reuse_port=allow_reuse_port,
                                                   backlog=backlog)

    async def serve_forever(self):
        if self.server is None:
            self.server = await self.server_factory
            self.serving.set_result(True)
            await self.server.serve_forever()
        else:
            raise RuntimeError("Can't call serve_forever on an already running server object")

    def server_close(self):
        for k,v in self.active_connections.items():
            _logger.warning("aborting active session {}".format(k))
            v.handler_task.cancel()
        self.active_connections = {}
        self.server.close()


class ModbusUdpServer:
    """
    A modbus threaded udp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    def __init__(self, context, framer=None, identity=None, address=None,
                 handler=None, allow_reuse_address=False,
                 allow_reuse_port=False,
                 defer_start=False,
                 backlog=20,
                 loop=None,
                 **kwargs):
        """ Overloaded initializer for the socket server

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
        """
        self.loop = loop or asyncio.get_event_loop()
        self.decoder = ServerDecoder()
        self.framer = framer  or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.address = address or ("", Defaults.Port)
        self.handler = handler or ModbusDisconnectedRequestHandler
        self.ignore_missing_slaves = kwargs.get('ignore_missing_slaves',
                                                Defaults.IgnoreMissingSlaves)
        self.broadcast_enable = kwargs.get('broadcast_enable',
                                           Defaults.broadcast_enable)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        self.protocol = None
        self.endpoint = None
        self.on_connection_terminated = None
        self.stop_serving = self.loop.create_future()
        self.serving = self.loop.create_future() # asyncio future that will be done once server has started
        self.server_factory = self.loop.create_datagram_endpoint(lambda: self.handler(self),
                                                                 local_addr=self.address,
                                                                 reuse_address=allow_reuse_address,
                                                                 reuse_port=allow_reuse_port,
                                                                 allow_broadcast=True)

    async def serve_forever(self):
        if self.protocol is None:
            self.protocol, self.endpoint = await self.server_factory
            self.serving.set_result(True)
            await self.stop_serving
        else:
            raise RuntimeError("Can't call serve_forever on an already running server object")

    def server_close(self):
        self.stop_serving.set_result(True)
        if self.endpoint.handler_task is not None:
            self.endpoint.handler_task.cancel()

        self.protocol.close()



class ModbusSerialServer(object):
    """
    A modbus threaded serial socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    handler = None

    def __init__(self, context, framer=None, identity=None, **kwargs): # pragma: no cover
        """ Overloaded initializer for the socket server

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
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
        """
        raise NotImplementedException


# --------------------------------------------------------------------------- #
# Creation Factories
# --------------------------------------------------------------------------- #
async def StartTcpServer(context=None, identity=None, address=None,
                         custom_functions=[], defer_start=True, **kwargs):
    """ A factory to start and run a tcp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param defer_start: if set, a coroutine which can be started and stopped
            will be returned. Otherwise, the server will be immediately spun
            up without the ability to shut it off from within the asyncio loop
    :param ignore_missing_slaves: True to not send errors on a request to a
                                      missing slave
    :return: an initialized but inactive server object coroutine
    """
    framer = kwargs.pop("framer", ModbusSocketFramer)
    server = ModbusTcpServer(context, framer, identity, address, **kwargs)

    for f in custom_functions:
        server.decoder.register(f) # pragma: no cover

    if not defer_start:
        await server.serve_forever()

    return server




async def StartUdpServer(context=None, identity=None, address=None,
                   custom_functions=[], defer_start=True, **kwargs):
    """ A factory to start and run a udp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param framer: The framer to operate with (default ModbusSocketFramer)
    :param ignore_missing_slaves: True to not send errors on a request
                                    to a missing slave
    """
    framer = kwargs.pop('framer', ModbusSocketFramer)
    server = ModbusUdpServer(context, framer, identity, address, **kwargs)

    for f in custom_functions:
        server.decoder.register(f) # pragma: no cover

    if not defer_start:
        await server.serve_forever() # pragma: no cover

    return server



def StartSerialServer(context=None, identity=None,  custom_functions=[],
                      **kwargs):# pragma: no cover
    """ A factory to start and run a serial modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param custom_functions: An optional list of custom function classes
        supported by server instance.
    :param framer: The framer to operate with (default ModbusAsciiFramer)
    :param port: The serial port to attach to
    :param stopbits: The number of stop bits to use
    :param bytesize: The bytesize of the serial messages
    :param parity: Which kind of parity to use
    :param baudrate: The baud rate to use for the serial device
    :param timeout: The timeout to use for the serial device
    :param ignore_missing_slaves: True to not send errors on a request to a
                                  missing slave
    """
    raise NotImplementedException
    import serial
    framer = kwargs.pop('framer', ModbusAsciiFramer)
    server = ModbusSerialServer(context, framer, identity, **kwargs)
    for f in custom_functions:
        server.decoder.register(f)
    server.serve_forever()

def StopServer():
    """
    Helper method to stop Async Server
    """
    import warnings
    warnings.warn("deprecated API for asyncio. Call server_close() on server object returned by StartXxxServer",
                  DeprecationWarning)



# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = [
    "StartTcpServer", "StartUdpServer", "StartSerialServer"
]

