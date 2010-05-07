'''
Implementation of a Twisted Modbus Server
------------------------------------------

Example run::

    context = ModbusServerContext(d=[0,100], c=[0,100], h=[0,100], i=[0,100])
    reactor.listenTCP(502, ModbusServerFactory(context))
    reactor.run()
'''
from binascii import b2a_hex
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ServerFactory

from pymodbus.constants import Defaults
from pymodbus.factory import ServerDecoder
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusControlBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.interfaces import IModbusFramer
from pymodbus.mexceptions import *
from pymodbus.pdu import ModbusExceptions as merror

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger("pymodbus.server")

#---------------------------------------------------------------------------#
# Server
#---------------------------------------------------------------------------#
class ModbusProtocol(Protocol):
    ''' Implements a modbus server in twisted '''

    def connectionMade(self):
        ''' Callback for when a client connects
       
        Note, since the protocol factory cannot be accessed from the
        protocol __init__, the client connection made is essentially our
        __init__ method.     
        '''
        _logger.debug("Client Connected [%s]" % self.transport.getHost())
        self.framer = self.factory.framer(decoder=self.factory.decoder)

    def connectionLost(self, reason):
        '''
        Callback for when a client disconnects
        @param reason The client's reason for disconnecting
        '''
        _logger.debug("Client Disconnected")

    def dataReceived(self, data):
        '''
        Callback when we receive any data
        @param data The data sent by the client
        '''
        _logger.debug(" ".join([hex(ord(x)) for x in data]))
        # if not self.factory.control.ListenOnly:
        self.framer.processIncomingPacket(data, self.execute)

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
        #self.framer.populateResult(response)
        response.transaction_id = request.transaction_id
        response.unit_id = request.unit_id
        self.send(response)

    def send(self, message):
        '''
        Send a request (string) to the network
        @param message The unencoded modbus response
        '''
        #self.factory.control.Counter.BusMessage += 1
        pdu = self.framer.buildPacket(message)
        _logger.debug('send: %s' % b2a_hex(pdu))
        return self.transport.write(pdu)


class ModbusServerFactory(ServerFactory):
    '''
    Builder class for a modbus server

    This also holds the server datastore so that it is
    persisted between connections
    '''

    protocol = ModbusProtocol

    def __init__(self, store, framer=None, identity=None):
        ''' Overloaded initializer for the modbus factory

        If the identify structure is not passed in, the ModbusControlBlock
        uses its own empty structure.

        :param store: The ModbusServerContext datastore
        :param framer: The framer strategy to use
        :param identity: An optional identify structure

        '''
        self.decoder = ServerDecoder()
        if isinstance(framer, IModbusFramer):
            self.framer = framer
        else: self.framer = ModbusSocketFramer

        if isinstance(store, ModbusServerContext):
            self.store = store
        else: self.store = ModbusServerContext()

        self.control = ModbusControlBlock()
        if isinstance(identity, ModbusDeviceIdentification):
            self.control.Identity.update(identity)

#---------------------------------------------------------------------------# 
# Starting Factories
#---------------------------------------------------------------------------# 
def StartTcpServer(context, identity=None):
    ''' Helper method to start the Modbus Async TCP server
    :param context: The server data context
    :param identify: The server identity to use
    '''
    framer = ModbusSocketFramer
    reactor.listenTCP(Defaults.Port,
        ModbusServerFactory(store=context, framer=framer, identity=identity))
    reactor.run()

def StartUdpServer(context, identity=None):
    ''' Helper method to start the Modbus Async Udp server
    :param context: The server data context
    :param identify: The server identity to use
    '''
    framer = ModbusSocketFramer
    reactor.listenUDP(Defaults.Port,
        ModbusServerFactory(store=context, framer=framer, identity=identity))
    reactor.run()

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "StartTcpServer", "StartUdpServer"
]
