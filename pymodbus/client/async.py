"""
Implementation of a Modbus Client Using Twisted
--------------------------------------------------

This attempts to fire off requets in succession so as to work as fast as
possible, but still refrain from overloading the remote device (usually
very mediocre in hardware).

Example Run::

    def clientTest():
        requests = [ ReadCoilsRequest(0,99) ]
        p = reactor.connectTCP("localhost", 502, ModbusClientFactory(requests))
    
    if __name__ == "__main__":
       reactor.callLater(1, clientTest)
       reactor.run()

What follows is a quick layout of the client logic:

  #. Build request array and instantiate a client factory
  #. Defer it until the reactor is running
  #. Upon connection, instantiate the producer and pass it

     * A handle to the transport
     * A handle to the request array
     * A handle to a sent request handler
     * A handle to the current framing object

  #. It then sends a request and waits
  #..
  #. The protocol recieves data and processes its frame

     * If we have a valid frame, we decode it and add the result(7)
     * Otherwise we continue(6)

  #. Afterwards, we instruct the producer to send the next request
  #. <work with data>
  #. Upon adding a result

     * The factory uses the handler object to translate the TID to a request
         * Using the request paramaters, we corretly store the resulting data
         * Each result is put into the appropriate store

  #. When all the requests have been processed

     * we stop the producer
         * disconnect the protocol
         * return the factory results

TODO:

This is broken right now, and I have been to lazy to fix it
I need to modify this to return defers and maybe pump requests
into the producer.
"""
import struct
from zope.interface import implements

from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor
from twisted.internet.interfaces import IPullProducer

from pymodbus.factory import ClientDecoder
from pymodbus.mexceptions import *
from pymodbus.bit_read_message import *
from pymodbus.register_read_message import *
from pymodbus.transaction import ModbusSocketFramer

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger('pymodbus.client')

#---------------------------------------------------------------------------#
# Client Producer/Consumer
#---------------------------------------------------------------------------#
class ModbusMessageProducer:
    '''
    This is a simply pull producer that feeds requests to the modbus client
    '''

    implements(IPullProducer)
    __tid = 0

    def __init__(self, consumer, requests, handler, framer):
        ''' Sets up the producer to begin sending requests
        :param consumer: The consuming protocol to register with
        :param requests: Initialize the request list
        :param handler: We copy each message so we know what we were requesting
        :param framer: Framer object that is used to build the request
        '''
        self.requests = requests
        self.framer   = framer
        self.consumer = consumer
        self.handler  = handler

        if self.consumer:
            self.consumer.registerProducer(self, False)

    def resumeProducing(self):
        ''' Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        if self.requests:
            request = self.requests.pop()
            request.transaction_id = self.__getNextTID()
            self.handler[request.transaction_id] = request
            self.consumer.write(self.framer.buildPacket(request))
        else: self.consumer.unregisterProducer()

    def stopProducing(self):
        ''' I don't actually know yet, but they complain otherwise
        '''
        _logger.debug("Client stopped producing")
        self.consumer.unregisterProducer()

    def __getNextTID(self):
        ''' Used to retrieve the next transaction id
        :return: The next unique transaction id

        As the transaction identifier is represented with two
        bytes, the highest TID is 0xffff
        '''
        tid = ModbusMessageProducer.__tid
        ModbusMessageProducer.__tid = (1 +
            ModbusMessageProducer.__tid) & 0xffff
        return tid

#---------------------------------------------------------------------------#
# Client Protocols
#---------------------------------------------------------------------------#
class ModbusClientProtocol(Protocol):
    ''' Implements a modbus client in twisted
    '''

    def __init__(self, framer=ModbusSocketFramer(ClientDecoder())):
        ''' Initializes the framer module

        :param framer: The framer to use for the protocol
        '''
        self.done = False
        self.framer = framer

    def connectionMade(self):
        '''
        Called upon a successful connection. Is used to instantiate and
        run the producer.
        '''
        _logger.debug("Client connected to modbus serveR")
        self.producer = ModbusMessageProducer(self.transport,
                self.factory.requests, self.factory.handler, self.framer)

    def dataReceived(self, data):
        '''
        Get response, check for valid message, decode result
        :param data: The data returned from the server
        '''
        self.framer.processIncomingPacket(data, self.execute)
        if self.factory.requests:
            self.producer.resumeProducing()
        else: self.transport.loseConnection()

    def execute(self, result):
        ''' The callback to call with the resulting message
        :param request: The decoded request message
        '''
        self.factory.addResponse(result)

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

#---------------------------------------------------------------------------#
# Client Factories
#---------------------------------------------------------------------------#
class ModbusClientFactory(ClientFactory):
    ''' Simply persistant client protocol factory '''

    protocol = ModbusClientProtocol

    def __init__(self, requests=None, results=None):
        ''' Initializes a transaction to a modbus server
        :param requests: A list of requests to send to server
        :param results: A handle to the results
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
        ''' Initiated on protocol connection start
        :param connector: The connection handler
        '''
        _logger.debug("Client Connection Made")

    def clientConnectionLost(self, connector, reason):
        ''' If we still have pending requets, reconnect
        :param connector: The connection handler
        :param reason: The reason for a disconnection
        '''
        _logger.debug("Client Connection Lost")
        if self.requests:
            _logger.debug("Client Connection Reconnect")
            connector.connect()
        else: reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        ''' If this happens, alert the user
        :param connector: The connection handler
        :param reason: The reason for a disconnection
        '''
        _logger.debug("Client Connection Failed")

    #----------------------------------------------------------------------#
    # Extra Functions
    #----------------------------------------------------------------------#
    def addResponse(self, response):
        '''
        Callback for the client protocol that adds request responses
        :param response: The resulting message

        We only care about returned data from a read request. Everything
        else is simply ignored for now
        '''
        try:
            a = self.handler[response.transaction_id].address
            if isinstance(response, ReadCoilsResponse):
                self.results['ci'][a] = response.getBit(0)
            elif isinstance(response, ReadDiscreteInputsResponse):
                self.results['di'][a] = response.getBit(0)
            elif isinstance(response, ReadHoldingRegistersResponse):
                self.results['hr'][a] = response.registers[0]
            elif isinstance(response, ReadInputRegistersResponse):
                self.results['ir'][a] = response.registers[0]
            else: pass
            del self.handler[response.transaction_id].address
        except KeyError: pass

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ModbusMessageProducer",
    "ModbusClientProtocol", "ModbusClientFactory",
]
