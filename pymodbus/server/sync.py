'''
Implementation of a Threaded Modbus Server
------------------------------------------

'''
from binascii import b2a_hex
import SocketServer
import serial
import socket

from pymodbus.constants import Defaults
from pymodbus.factory import ServerDecoder
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import *
from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import ModbusExceptions as merror

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)


#---------------------------------------------------------------------------#
# Protocol Handlers
#---------------------------------------------------------------------------#
class ModbusBaseRequestHandler(SocketServer.BaseRequestHandler):
    ''' Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler.
    '''

    def setup(self):
        ''' Callback for when a client connects
        '''
        _logger.debug("Client Connected [%s:%s]" % self.client_address)
        self.running = True
        self.framer = self.server.framer(self.server.decoder)
        self.server.threads.append(self)

    def finish(self):
        ''' Callback for when a client disconnects
        '''
        _logger.debug("Client Disconnected [%s:%s]" % self.client_address)
        self.server.threads.remove(self)

    def execute(self, request):
        ''' The callback to call with the resulting message

        :param request: The decoded request message
        '''
        try:
            context = self.server.context[request.unit_id]
            response = request.execute(context)
        except Exception, ex:
            _logger.debug("Datastore unable to fulfill request: %s" % ex)
            response = request.doException(merror.SlaveFailure)
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self.send(response)

    #---------------------------------------------------------------------------#
    # Base class implementations
    #---------------------------------------------------------------------------#
    def handle(self):
        ''' Callback when we receive any data
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def send(self, message):
        ''' Send a request (string) to the network

        :param message: The unencoded modbus response
        '''
        raise NotImplementedException("Method not implemented by derived class")


class ModbusSingleRequestHandler(ModbusBaseRequestHandler):
    ''' Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler for a single client(serial clients)
    '''

    def handle(self):
        ''' Callback when we receive any data
        '''
        while self.running:
            try:
                data = self.request.recv(1024)
                if data:
                    if _logger.isEnabledFor(logging.DEBUG):
                        _logger.debug(" ".join([hex(ord(x)) for x in data]))
                    self.framer.processIncomingPacket(data, self.execute)
            except Exception, msg:
                # since we only have a single socket, we cannot exit
                _logger.error("Socket error occurred %s" % msg)

    def send(self, message):
        ''' Send a request (string) to the network

        :param message: The unencoded modbus response
        '''
        if message.should_respond:
            #self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: %s' % b2a_hex(pdu))
            return self.request.send(pdu)


class ModbusConnectedRequestHandler(ModbusBaseRequestHandler):
    ''' Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler for a connected protocol (TCP).
    '''

    def handle(self):
        ''' Callback when we receive any data
        '''
        while self.running:
            try:
                data = self.request.recv(1024)
                if not data: self.running = False
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug(" ".join([hex(ord(x)) for x in data]))
                # if not self.server.control.ListenOnly:
                self.framer.processIncomingPacket(data, self.execute)
            except socket.timeout: pass
            except socket.error, msg:
                _logger.error("Socket error occurred %s" % msg)
                self.running = False
            except: self.running = False

    def send(self, message):
        ''' Send a request (string) to the network

        :param message: The unencoded modbus response
        '''
        if message.should_respond:
            #self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: %s' % b2a_hex(pdu))
            return self.request.send(pdu)


class ModbusDisconnectedRequestHandler(ModbusBaseRequestHandler):
    ''' Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler for a disconnected protocol (UDP). The
    only difference is that we have to specify who to send the
    resulting packet data to.
    '''

    def handle(self):
        ''' Callback when we receive any data
        '''
        while self.running:
            try:
                data, self.request = self.request
                if not data: self.running = False
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug(" ".join([hex(ord(x)) for x in data]))
                # if not self.server.control.ListenOnly:
                self.framer.processIncomingPacket(data, self.execute)
            except socket.timeout: pass
            except socket.error, msg:
                _logger.error("Socket error occurred %s" % msg)
                self.running = False
            except: self.running = False

    def send(self, message):
        ''' Send a request (string) to the network

        :param message: The unencoded modbus response
        '''
        if message.should_respond:
            #self.server.control.Counter.BusMessage += 1
            pdu = self.framer.buildPacket(message)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug('send: %s' % b2a_hex(pdu))
            return self.request.sendto(pdu, self.client_address)


#---------------------------------------------------------------------------#
# Server Implementations
#---------------------------------------------------------------------------#
class ModbusTcpServer(SocketServer.ThreadingTCPServer):
    '''
    A modbus threaded tcp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    '''

    def __init__(self, context, framer=None, identity=None, address=None):
        ''' Overloaded initializer for the socket server

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        '''
        self.threads = []
        self.decoder = ServerDecoder()
        self.framer  = framer  or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.address = address or ("", Defaults.Port)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        SocketServer.ThreadingTCPServer.__init__(self,
            self.address, ModbusConnectedRequestHandler)

    def process_request(self, request, client):
        ''' Callback for connecting a new client thread

        :param request: The request to handle
        :param client: The address of the client
        '''
        _logger.debug("Started thread to serve client at " + str(client))
        SocketServer.ThreadingTCPServer.process_request(self, request, client)

    def server_close(self):
        ''' Callback for stopping the running server
        '''
        _logger.debug("Modbus server stopped")
        self.socket.close()
        for thread in self.threads:
            thread.running = False


class ModbusUdpServer(SocketServer.ThreadingUDPServer):
    '''
    A modbus threaded udp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    '''

    def __init__(self, context, framer=None, identity=None, address=None):
        ''' Overloaded initializer for the socket server

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure
        :param address: An optional (interface, port) to bind to.
        '''
        self.threads = []
        self.decoder = ServerDecoder()
        self.framer  = framer  or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()
        self.address = address or ("", Defaults.Port)

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        SocketServer.ThreadingUDPServer.__init__(self,
            self.address, ModbusDisconnectedRequestHandler)

    def process_request(self, request, client):
        ''' Callback for connecting a new client thread

        :param request: The request to handle
        :param client: The address of the client
        '''
        packet, socket = request # TODO I might have to rewrite
        _logger.debug("Started thread to serve client at " + str(client))
        SocketServer.ThreadingUDPServer.process_request(self, request, client)

    def server_close(self):
        ''' Callback for stopping the running server
        '''
        _logger.debug("Modbus server stopped")
        self.socket.close()
        for thread in self.threads:
            thread.running = False


class ModbusSerialServer(object):
    '''
    A modbus threaded udp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    '''

    def __init__(self, context, framer=None, identity=None, **kwargs):
        ''' Overloaded initializer for the socket server

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

        '''
        self.threads = []
        self.decoder = ServerDecoder()
        self.framer  = framer  or ModbusAsciiFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        self.device   = kwargs.get('port', 0)
        self.stopbits = kwargs.get('stopbits', Defaults.Stopbits)
        self.bytesize = kwargs.get('bytesize', Defaults.Bytesize)
        self.parity   = kwargs.get('parity',   Defaults.Parity)
        self.baudrate = kwargs.get('baudrate', Defaults.Baudrate)
        self.timeout  = kwargs.get('timeout',  Defaults.Timeout)
        self.socket   = None
        self._connect()
        self.is_running = True

    def _connect(self):
        ''' Connect to the serial server

        :returns: True if connection succeeded, False otherwise
        '''
        if self.socket: return True
        try:
            self.socket = serial.Serial(port=self.device, timeout=self.timeout,
                bytesize=self.bytesize, stopbits=self.stopbits,
                baudrate=self.baudrate, parity=self.parity)
        except serial.SerialException, msg:
            _logger.error(msg)
        return self.socket != None

    def _build_handler(self):
        ''' A helper method to create and monkeypatch
            a serial handler.

        :returns: A patched handler
        '''
        request = self.socket
        request.send = request.write
        request.recv = request.read
        handler = ModbusSingleRequestHandler(request,
            (self.device, self.device), self)
        return handler

    def serve_forever(self):
        ''' Callback for connecting a new client thread

        :param request: The request to handle
        :param client: The address of the client
        '''
        _logger.debug("Started thread to serve client")
        handler = self._build_handler()
        while self.is_running:
            handler.handle()

    def server_close(self):
        ''' Callback for stopping the running server
        '''
        _logger.debug("Modbus server stopped")
        self.is_running = False
        self.socket.close()


#---------------------------------------------------------------------------#
# Creation Factories
#---------------------------------------------------------------------------#
def StartTcpServer(context=None, identity=None, address=None):
    ''' A factory to start and run a tcp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    '''
    framer = ModbusSocketFramer
    server = ModbusTcpServer(context, framer, identity, address)
    server.serve_forever()


def StartUdpServer(context=None, identity=None, address=None):
    ''' A factory to start and run a udp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param address: An optional (interface, port) to bind to.
    '''
    framer = ModbusSocketFramer
    server = ModbusUdpServer(context, framer, identity, address)
    server.serve_forever()


def StartSerialServer(context=None, identity=None, **kwargs):
    ''' A factory to start and run a udp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    :param port: The serial port to attach to
    :param stopbits: The number of stop bits to use
    :param bytesize: The bytesize of the serial messages
    :param parity: Which kind of parity to use
    :param baudrate: The baud rate to use for the serial device
    :param timeout: The timeout to use for the serial device
    '''
    framer = ModbusAsciiFramer
    server = ModbusSerialServer(context, framer, identity, **kwargs)
    server.serve_forever()

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "StartTcpServer", "StartUdpServer", "StartSerialServer"
]
