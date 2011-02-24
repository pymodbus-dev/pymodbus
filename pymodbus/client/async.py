"""
Implementation of a Modbus Client Using Twisted
--------------------------------------------------

Example Run::

    from pymodbus.client.async import ModbusClientFactory
    from pymodbus.bit_read_message import ReadCoilsRequest

    def clientTest():
        requests = [ ReadCoilsRequest(0,99) ]
        p = reactor.connectTCP("localhost", 502, ModbusClientFactory(requests))
    
    if __name__ == "__main__":
       reactor.callLater(1, clientTest)
       reactor.run()
"""
import struct
from collections import deque

from twisted.internet import reactor, defer, protocol

from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.client.common import ModbusClientMixin

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Client Protocols
#---------------------------------------------------------------------------#
class ModbusClientProtocol(protocol.Protocol, ModbusClientMixin):
    '''
    This represents the base modbus client protocol.  All the application
    layer code is deferred to a higher level wrapper.
    '''
    __tid = 0

    def __init__(self, framer=None):
        ''' Initializes the framer module

        :param framer: The framer to use for the protocol
        '''
        self.framer = framer or ModbusSocketFramer(ClientDecoder())
        self._requests = deque() # link queue to tid
        self._connected = False

    def connectionMade(self):
        ''' Called upon a successful client connection.
        '''
        _logger.debug("Client connected to modbus server")
        self._connected = True

    def connectionLost(self, reason):
        ''' Called upon a client disconnect

        :param reason: The reason for the disconnect
        '''
        _logger.debug("Client disconnected from modbus server: %s" % reason)
        self._connected = False

    def dataReceived(self, data):
        ''' Get response, check for valid message, decode result

        :param data: The data returned from the server
        '''
        self.framer.processIncomingPacket(data, self._callback)

    def execute(self, request):
        ''' Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        request.transaction_id = self.__getNextTID()
        #self.handler[request.transaction_id] = request
        packet = self.framer.buildPacket(request)
        self.transport.write(packet)
        return self._buildResponse()

    def _callback(self, reply):
        ''' The callback to call with the response message

        :param reply: The decoded response message
        '''
        # todo errback/callback
        if self._requests:
            self._requests.popleft().callback(reply)

    def _buildResponse(self):
        ''' Helper method to return a deferred response
        for the current request.

        :returns: A defer linked to the latest request
        '''
        if not self._connected:
            return defer.fail(ConnectionException('Client is not connected'))

        d = defer.Deferred()
        self._requests.append(d)
        return d

    def __getNextTID(self):
        ''' Used to retrieve the next transaction id
        :return: The next unique transaction id

        As the transaction identifier is represented with two
        bytes, the highest TID is 0xffff

        ..todo:: Remove this and use the transaction manager
        '''
        tid = (ModbusClientProtocol.__tid + 1) & 0xffff
        ModbusClientProtocol.__tid = tid
        return tid

    #----------------------------------------------------------------------#
    # Extra Functions
    #----------------------------------------------------------------------#
    #if send_failed:
    #       if self.retry > 0:
    #               deferLater(clock, self.delay, send, message)
    #               self.retry -= 1

#---------------------------------------------------------------------------#
# Client Factories
#---------------------------------------------------------------------------#
class ModbusClientFactory(protocol.ReconnectingClientFactory):
    ''' Simple client protocol factory '''

    protocol = ModbusClientProtocol

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ModbusClientProtocol", "ModbusClientFactory",
]
