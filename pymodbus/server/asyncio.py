"""
Implementation of a Threaded Modbus Server
------------------------------------------

"""
from binascii import b2a_hex
import serial
import socket
import traceback

import asyncio
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
_logger.setLevel(logging.DEBUG)


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
            self.handler_task = asyncio.create_task(self.handle())
        except Exception as ex:
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
            exc_ = self.handler_task.exception() # this will contain any pending exceptions
            self.handler_task.cancel()
            _logger.debug("Socket [%s] closed" % transport.get_extra_info('sockname'))

            if exc is not None:
                __logger.debug("Client Disconnection [%s:%s] due to %s" % (*self.client_address, exc))
            else:
                _logger.debug("Client Disconnected [%s:%s]" % self.client_address)
            self.server.active_connections.pop(self.client_address)
            self.running = False

        except Exception as ex:
            _logger.debug("Datastore unable to fulfill request: "
                      "%s; %s", ex, traceback.format_exc())

    async def handle(self):
        """Asyncio coroutine which represents a single conversation between
        the modbus slave and master

        Once the client connection is established, the data chunks will be
        fed to this coroutine via the asyncio.Queue object which is fed by
        the ModbusBaseRequestHandler class's callback Future.

        This function will execute without blocking in the while-loop and
        yield to the asyncio event loop when the is exhausted.
        As a result, multiple clients can be interleaved without any
        interference between them.

        To respond to Modbus...Server.server_close() (which clears each
        handler's self.running), derive from this class to provide an
        alternative handler that awakens from time to time when no input is
        available and checks self.running.
        Use Modbus...Server( handler=... ) keyword to supply the alternative
        request handler class.

        """
        reset_frame = False
        while self.running:
            try:
                units = self.server.context.slaves()
                data = await self._recv_()
                if isinstance(data, tuple):
                    data, *rest = data # rest carries possible contextual information
                else:
                    rest = (None,) # empty tuple

                if not data:
                    self.running = False
                    # data = b''  # is this required? Once the running
                    # flag is unset, the whole thing comes down anyways
                else:
                    if not isinstance(units, (list, tuple)):
                        units = [units]
                    # if broadcast is enabled make sure to
                    # process requests to address 0
                    if self.server.broadcast_enable:
                        if 0 not in units:
                            units.append(0)

                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug('Handling data: ' + hexlify_packets(data))

                single = self.server.context.single
                self.framer.processIncomingPacket(data, lambda x: self.execute(x, *rest) ,
                                                  units, single=single)

            except asyncio.TimeoutError as msg:
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug("Socket timeout occurred %s", msg)
                reset_frame = True
            except asyncio.InvalidStateError as e:
                _logger.error("Socket error occurred %s" % e)
                self.running = False
            finally:
                if reset_frame:
                    self.framer.resetFrame()
                    reset_frame = False

    def execute(self, request, *rest):
        """ The callback to call with the resulting message

        :param request: The decoded request message
        """
        broadcast = False
        try:
            print(request)
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
            self.send(response, *rest)


    def send(self, message, *rest):
        if message.should_respond:
            # self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: [%s]- %s' % (message, b2a_hex(pdu)))
            print(rest)
            if rest == (None,):
                self._send_(pdu)
            else:
                self._send_(pdu, *rest)

    # ----------------------------------------------------------------------- #
    # Derived class implementations
    # ----------------------------------------------------------------------- #

    def _send_(self, data):
        """ Send a request (string) to the network

        :param message: The unencoded modbus response
        """
        raise NotImplementedException("Method not implemented "
                                      "by derived class")
    async def _recv_(self):
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
        _logger.debug("TCP client disconnected [%s:%s]" % self.client_address)
        self.server.active_connections.pop(self.client_address)


    def data_received(self,data):
        """
        asyncio.Protocol: (TCP) Called when some data is received.
        data is a non-empty bytes object containing the incoming data.
        """
        asyncio.create_task(self.receive_queue.put(data))

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
        asyncio.create_task(self.receive_queue.put((data, addr)))

    def error_received(self,exc):
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

        self.server = None
        self.server_factory = self.loop.create_server(lambda : self.handler(self),
                                                   *self.address,
                                                   reuse_address=allow_reuse_address,
                                                   reuse_port=allow_reuse_port,
                                                   backlog=backlog,
                                                   start_serving=not defer_start)

    async def serve_forever(self):
        if self.server is None:
            self.server = await self.server_factory

        await self.server.serve_forever()

    def server_close(self):
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
        self.server_factory = self.loop.create_datagram_endpoint(lambda: self.handler(self),
                                                                 local_addr=self.address,
                                                                 reuse_address=allow_reuse_address,
                                                                 reuse_port=allow_reuse_port,
                                                                 allow_broadcast=True)

    async def serve_forever(self):
        if self.protocol is None:
            self.protocol, self.endpoint = await self.server_factory

        await self.on_connection_terminated

    def server_close(self):
        self.endpoint.close()



class ModbusSerialServer(object):
    """
    A modbus threaded serial socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    """

    handler = None

    def __init__(self, context, framer=None, identity=None, **kwargs):
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
        server.decoder.register(f)

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
        server.decoder.register(f)

    if not defer_start:
        await server.serve_forever()

    return server



def StartSerialServer(context=None, identity=None,  custom_functions=[],
                      **kwargs):
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
    framer = kwargs.pop('framer', ModbusAsciiFramer)
    server = ModbusSerialServer(context, framer, identity, **kwargs)
    for f in custom_functions:
        server.decoder.register(f)
    server.serve_forever()

# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = [
    "StartTcpServer", "StartUdpServer", "StartSerialServer"
]

