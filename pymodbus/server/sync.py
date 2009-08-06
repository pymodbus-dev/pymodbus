'''
Implementation of a Threaded Modbus Server
------------------------------------------

Example run::

    context = ModbusServerContext(d=[0,100], c=[0,100], h=[0,100], i=[0,100])
    server = ModbusTcpServer(store, context, identity)
    server.serve_forever()
'''
import SocketServer

from pymodbus.constants import Defaults
from pymodbus.factory import decodeModbusResponsePDU
from pymodbus.factory import decodeModbusRequestPDU
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import ModbusTCPFramer
from pymodbus.interfaces import IModbusFramer
from pymodbus.mexceptions import *
from pymodbus.pdu import ModbusExceptions as merror
from binascii import b2a_hex

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger("pymodbus.server")

#---------------------------------------------------------------------------#
# Server
#---------------------------------------------------------------------------#
class ModbusRequestHandler(SocketServer.BaseRequestHandler):
    ''' Implements the modbus server protocol

    This uses the socketserver.BaseRequestHandler to implement
    the client handler.
    '''

    def __init__(self):
        ''' Initializes server '''
        self.frame = ModbusTCPFramer()#self.factory.framer()

    def setup(self):
        ''' Callback for when a client connects '''
        _logger.debug("Client Connected [%s]" % self.client_address)
        #self.factory.control.counter + 1 ?

    def finish(self):
        ''' Callback for when a client disconnects
        '''
        _logger.debug("Client Disconnected [%s]" % self.client_address)
        #self.factory.control.counter - 1 ?

    def handle(self):
        ''' Callback when we receive any data
        '''
        # if self.factory.control.isListenOnly == False:
        data = self.request.recv(1024)
        _logger.debug(" ".join([hex(ord(x)) for x in data]))
        self.frame.addToFrame(data)
        while self.frame.isFrameReady():
            if self.frame.checkFrame():
                result = self.decode(self.frame.getFrame())
                if result is None:
                    raise ModbusIOException("Unable to decode response")
                self.frame.populateResult(result)
                self.frame.advanceFrame()
                self.execute(result) # defer or push to a thread?
            else: break

#---------------------------------------------------------------------------#
# Extra Helper Functions
#---------------------------------------------------------------------------#
    def execute(self, request):
        '''
        Executes the request and returns the result
        @param request The decoded request message
        '''
        try:
            response = request.execute(self.factory.store)
        except Exception, ex:
            _logger.debug("Datastore unable to fulfill request %s" % ex)
            response = request.doException(merror.SlaveFailure)
        response.transaction_id = request.transaction_id
        response.uint_id = request.unit_id
        self.send(response)

    def send(self, message):
        '''
        Send a request (string) to the network
        @param message The unencoded modbus response
        '''
        pdu = self.frame.buildPacket(message)
        _logger.debug('send: %s' % b2a_hex(pdu))
        return self.request.send(pdu)

    def decode(self, message):
        '''
        Decodes a request packet
        @param message The raw modbus request packet
        @return The decoded modbus message or None if error
        '''
        try:
            return decodeModbusRequestPDU(message)
        except ModbusException, er:
            _logger.warn("Unable to decode request %s" % er)
        return None

class ModbusTCPServer(SocketServer.ThreadingTCPServer):
    '''
    A modbus threaded tcp socket server

    We inherit and overload the socket server so that we
    can control the client threads as well as have a single
    server context instance.
    '''

    def __init__(self, context, framer=None, identity=None):
        ''' Overloaded initializer for the socket server
        :param context: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.
        '''
        if isinstance(framer, IModbusFramer):
            self.framer = framer
        else: self.framer = ModbusTCPFramer

        if isinstance(store, ModbusServerContext):
            self.context = context
        else: self.context = ModbusServerContext()
        self.control = ModbusControlBlock()

        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity = identity
        self.threads = []
        SocketServer.ThreadingTCPServer.__init__(self,
            ("", Defaults.Port), ModbusRequestHandler)

    def process_request(self, request, client):
        ''' Callback for connecting a new client thread
        :param request: The request to handle
        :param client: The address of the client
        '''
        _logger.debug("Started thread to serve client at " + str(client_address))
        SocketServer.ThreadingTCPServer.process_request(
                self, request, client)

    def server_close(self):
        ''' Callback for stopping the running server
        '''
        _logger.debug("Modbus server stopped")
        self.socket.close()
        for t in self.threads:
            t.run = False

#---------------------------------------------------------------------------# 
# Starting Factories
#---------------------------------------------------------------------------# 
def StartTcpServer(self, context=None, framer=None, identity=None):
    ''' A factory to start and run a modbus server
    :param context: The ModbusServerContext datastore
    :param framer: The framer strategy to use
    :param identity: An optional identify structure
    '''
    server = ModbusTcpServer(context, framer, identity)
    server.serve_forever()

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ModbusTcpServer",
    "StartTcpServer",
]
