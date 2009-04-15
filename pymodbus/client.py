'''
Implementation of a modbus client using Twisted

This attempts to fire off requets in succession so as to work as fast as
possible, but still refrain from overloading the remote device (usually
very mediocre in hardware)

Example Run:
def clientTest():
        requests = [ ReadCoilsRequest(0,99) ]
        p = reactor.connectTCP("localhost", 502, ModbusClientFactory(requests))

if __name__ == "__main__":
        reactor.callLater(1, clientTest)
        reactor.run()

What follows is a quick layout of the client logic:
  1. Build request array and instantiate a client factory
  2. Defer it until the reactor is running
  3. Upon connection, instantiate the producer and pass it
     * A handle to the transport
     * A handle to the request array
     * A handle to a sent request handler
     * A handle to the current framing object
  4. It then sends a request and waits
  ...
  5. The protocol recieves data and processes its frame
     * If we have a valid frame, we decode it and add the result(7)
     * Otherwise we continue(6)
  6. Afterwards, we instruct the producer to send the next request
  ...
  7. Upon adding a result
     * The factory uses the handler object to translate the TID to a request
         * Using the request paramaters, we corretly store the resulting data
         * Each result is put into the appropriate store
  7. When all the requests have been processed
     * we stop the producer
         * disconnect the protocol
         * return the factory results

TODO
  * Build a repeated request producer?
  * Simplify request <-> response linking
'''
from zope.interface import implements

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor
from twisted.internet.interfaces import IPullProducer

from pymodbus.factory import decodeModbusResponsePDU
from pymodbus.mexceptions import *
from pymodbus.bit_read_message import ReadBitsResponseBase
from pymodbus.register_read_message import ReadRegistersResponseBase
from pymodbus.transaction import ModbusTCPFramer

import struct
import logging
_logger = logging.getLogger('pymodbus.client')


#---------------------------------------------------------------------------#
# Client Producer/Consumer
#---------------------------------------------------------------------------#
class ModbusMessageProducer:
    '''
    This is a simply pull producer that feeds requets to the modbus client
    '''

    implements(IPullProducer)
    __tid = 0

    def __init__(self, consumer, requests, handler, framer):
        '''
        Sets up the producer to begin sending requests
        @param consumer The consuming protocol to register with
        @param requests Initialize the request list
        @param handler We copy each message so we know what we were requesting
        @param framer Framer object that is used to build the request
        '''
        self.requests = requests
        self.framer = framer
        self.consumer = consumer
        self.handler = handler

        if self.consumer:
            self.consumer.registerProducer(self, False)

    def resumeProducing(self):
        '''
        Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        if self.requests:
            request = self.requests.pop()
            request.transaction_id = self.__getNextTID()
            self.handler[request.transaction_id] = request
            self.consumer.write(self.framer.buildPacket(request))
        else: self.consumer.unregisterProducer()

    def stopProducing(self):
        ''' I don't actually know yet, but they complain otherwise '''
        _logger.debug("Client stopped producing")
        self.consumer.unregisterProducer()

    def __getNextTID(self):
        '''
        Used internally to handle the transaction identifiers
        As the transaction identifier is represented with two
        bytes, the highest TID is 0xffff
        '''
        tid = self.__tid
        self.__tid = (1 + self.__tid) & 0xffff
        return tid

#---------------------------------------------------------------------------#
# Client Protocols
#---------------------------------------------------------------------------#
class ModbusClientProtocol(Protocol):
    ''' Implements a modbus client in twisted '''

    def __init__(self):
        '''
        Initializes the framer module
        '''
        self.done = False
        self.framer = ModbusTCPFramer()

    def connectionMade(self):
        '''
        Called upon a successful connection. Is used to instantiate and
        run the producer.
        '''
        self.producer = ModbusMessageProducer(self.transport,
                self.factory.requests, self.factory.handler, self.framer)

    def dataReceived(self, data):
        '''
        Get response, check for valid message, decode result
        @param data The data returned from the server
        '''
        _logger.debug("[R]" + " ".join([hex(ord(x)) for x in data]))
        self.framer.addToFrame(data)
        while self.framer.isFrameReady():
            if self.framer.checkFrame():
                result = self.decode(self.framer.getFrame())
                if result is None:
                    raise ModbusIOException("Unable to decode response")
                self.framer.populateResult(result)
                self.framer.advanceFrame()
                self.factory.addResponse(result)
            else: break
        if self.factory.requests:
            self.producer.resumeProducing()
        else: self.transport.loseConnection()

    #----------------------------------------------------------------------#
    # Extra Functions
    #----------------------------------------------------------------------#
    #if send_failed:
    #       if self.retry > 0:
    #               deferLater(clock, self.delay, send, message)
    #               self.retry -= 1
    #----------------------------------------------------------------------#
    #def send(self, message):
    #       '''
    #       Send a request (string) to the network
    #       @param message The unencoded modbus request
    #       '''
    #       return self.transport.write(self.framer.buildPacket(message))

    def decode(self, message):
        '''
        Wrapper to decode a resulting packet
        @param message The raw packet to decode
        '''
        try:
            return decodeModbusResponsePDU(message)
        except ModbusException, er:
            _logger.debug("Unable to decode response")
        return None

#---------------------------------------------------------------------------#
# Client Factories
#---------------------------------------------------------------------------#
class ModbusClientFactory(ClientFactory):
    ''' Simply persistant client protocol factory '''

    protocol = ModbusClientProtocol

    def __init__(self, requests=None, results=None):
        '''
        Initializes a transaction to a modbus server
        @param requests A list of requests to send to server
        '''
        self.handler = {}
        if isinstance(requests, list):
            self.requests = requests
        elif requests:
            self.requests = [requests]
        else: pass

        # initialize the results structure
        if results != None:
            self.results = results
        else:
            self.results = {}
        for key in ('ci', 'di', 'hr', 'ir'): self.results[key]= {}

    #def buildProtocol(self, addr):
    #       p = protocol.ClientFactory.buildProtocol(self, addr)
    #       # handle timeout/retry?
    #       return p

    def startedConnecting(self, connector):
        '''
        Initiated on protocol connection start
        @param connector The connection handler
        '''
        _logger.debug("Client Connection Made")

    def clientConnectionLost(self, connector, reason):
        '''
        If we still have pending requets, reconnect
        @param connector The connection handler
        @param reason The reason for a disconnection
        '''
        _logger.debug("Client Connection Lost")
        if self.requests:
            _logger.debug("Client Connection Reconnect")
            connector.connect()
        else: reactor.stop()


    def clientConnectionFailed(self, connector, reason):
        '''
        If this happens, alert the user
        @param connector The connection handler
        @param reason The reason for a disconnection
        '''
        _logger.debug("Client Connection Failed")

    #----------------------------------------------------------------------#
    # Extra Functions
    #----------------------------------------------------------------------#
    def addResponse(self, response):
        '''
        Callback for the client protocol that adds request responses
        @param response The resulting message

        We only care about returned data from a read request. Everything
        else is simply ignored for now
        '''
        try:
            a = self.handler[response.transaction_id].address
            if isinstance(response, ReadCoilsResponse):
                self.results['ci'][a] = response.getBit[0]
            elif isinstance(response, ReadDiscreteInputsResponse):
                self.results['di'][a] = response.getBit[0]
            elif isinstance(response, ReadHoldingRegistersResponse):
                self.results['hr'][a] = response.registers[0]
            elif isinstance(response, ReadInputRegistersResponse):
                self.results['ir'][a] = response.registers[0]
            else: pass
            del self.handler[response.transaction_id].address
        except KeyError: pass
