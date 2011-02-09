'''
Implementation of a Threaded Modbus Server
------------------------------------------

'''
from binascii import b2a_hex
import SocketServer
import serial, socket

from pymodbus.constants import Defaults
from pymodbus.factory import ServerDecoder
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import *
from pymodbus.interfaces import IModbusFramer
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ModbusExceptions as merror

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Server
#---------------------------------------------------------------------------#
class ModbusRequestHandler(SocketServer.BaseRequestHandler):
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

    def handle(self):
        ''' Callback when we receive any data
        '''
        while self.running:
            try:
                data = self.request.recv(1024)
                _logger.debug(" ".join([hex(ord(x)) for x in data]))
                # if not self.server.control.ListenOnly:
                self.framer.processIncomingPacket(data, self.execute)
            except socket.timeout: pass
            except socket.error, msg:
                _logger.error("Socket error occurred %s" % msg)
                self.running = False
            except: self.running = False

#---------------------------------------------------------------------------#
# Extra Helper Functions
#---------------------------------------------------------------------------#
    def execute(self, request):
        ''' The callback to call with the resulting message

        :param request: The decoded request message
        '''
        try:
            context = self.server.context[request.unit_id]
            response = request.execute(context)
        except Exception, ex:
            _logger.debug("Datastore unable to fulfill request %s" % ex)
            response = request.doException(merror.SlaveFailure)
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self.send(response)

    def send(self, message):
        ''' Send a request (string) to the network

        :param message: The unencoded modbus response
        '''
        #self.server.control.Counter.BusMessage += 1
        pdu = self.framer.buildPacket(message)
        _logger.debug('send: %s' % b2a_hex(pdu))
        return self.request.send(pdu)

    def decode(self, message):
        ''' Decodes a request packet

        :param message: The raw modbus request packet
        :returns: The decoded modbus message or None if error
        '''
        try:
            return decodeModbusRequestPDU(message)
        except ModbusException, er:
            _logger.warn("Unable to decode request %s" % er)
        return None

class ModbusTcpServer(SocketServer.ThreadingTCPServer):
    '''
    A modbus threaded tcp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    '''

    def __init__(self, context, framer=None, identity=None):
        ''' Overloaded initializer for the socket server

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure

        '''
        self.threads = []
        self.decoder = ServerDecoder()
        self.framer  = framer  or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        SocketServer.ThreadingTCPServer.__init__(self,
            ("", Defaults.Port), ModbusRequestHandler)

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
        for thread in self.threads: thread.running = False

class ModbusUdpServer(SocketServer.ThreadingUDPServer):
    '''
    A modbus threaded udp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    '''

    def __init__(self, context, framer=None, identity=None):
        ''' Overloaded initializer for the socket server

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure

        '''
        self.threads = []
        self.decoder = ServerDecoder()
        self.framer  = framer  or ModbusSocketFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        SocketServer.ThreadingUDPServer.__init__(self,
            ("", Defaults.Port), ModbusRequestHandler)

    def process_request(self, request, client):
        ''' Callback for connecting a new client thread

        :param request: The request to handle
        :param client: The address of the client
        '''
        _logger.debug("Started thread to serve client at " + str(client))
        SocketServer.ThreadingUDPServer.process_request(self, request, client)

    def server_close(self):
        ''' Callback for stopping the running server
        '''
        _logger.debug("Modbus server stopped")
        self.socket.close()
        for thread in self.threads: thread.running = False

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

        '''
        self.threads = []
        self.decoder = ServerDecoder()
        self.framer  = framer  or ModbusAsciiFramer
        self.context = context or ModbusServerContext()
        self.control = ModbusControlBlock()

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

        self.device   = kwargs.get('device', 0)
        self.stopbits = kwargs.get('stopbits', Defaults.Stopbits)
        self.bytesize = kwargs.get('bytesize', Defaults.Bytesize)
        self.parity   = kwargs.get('parity',   Defaults.Parity)
        self.baudrate = kwargs.get('baudrate', Defaults.Baudrate)
        self.timeout  = kwargs.get('timeout',  Defaults.Timeout)
        self.socket   = None
        self._connect()

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
            self.close()
        return self.socket != None

    def _build_handler(self):
        ''' A helper method to create and monkeypatch
            a serial handler.

        :returns: A patched handler
        '''
        request = self.socket
        request.send = request.write
        request.recv = request.read
        handler = ModbusRequestHandler(request, ('127.0.0.1', self.device), self)
        return handler

    def serve_forever(self):
        ''' Callback for connecting a new client thread

        :param request: The request to handle
        :param client: The address of the client
        '''
        _logger.debug("Started thread to serve client")
        handler = self._build_handler()
        while True: handler.handle()

    def server_close(self):
        ''' Callback for stopping the running server
        '''
        _logger.debug("Modbus server stopped")
        self.socket.close()

#---------------------------------------------------------------------------# 
# Creation Factories
#---------------------------------------------------------------------------# 
def StartTcpServer(context=None, identity=None):
    ''' A factory to start and run a tcp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    '''
    framer = ModbusSocketFramer
    server = ModbusTcpServer(context, framer, identity)
    server.serve_forever()

def StartUdpServer(context=None, identity=None):
    ''' A factory to start and run a udp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
    '''
    framer = ModbusSocketFramer
    server = ModbusUdpServer(context, framer, identity)
    server.serve_forever()

def StartSerialServer(context=None, identity=None, **kwargs):
    ''' A factory to start and run a udp modbus server

    :param context: The ModbusServerContext datastore
    :param identity: An optional identify structure
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
