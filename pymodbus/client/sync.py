"""
Implementation of a Modbus Client Using Sockets
------------------------------------------------

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
"""
import socket
import struct

from pymodbus.constants import Defaults
from pymodbus.factory import ClientDecoder
from pymodbus.mexceptions import *
from pymodbus.bit_read_message import *
from pymodbus.register_read_message import *
from pymodbus.transaction import ModbusTCPFramer

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger('pymodbus.client')

#---------------------------------------------------------------------------#
# Client Producer/Consumer
#---------------------------------------------------------------------------#
class ModbusTransactionManager:
    '''
    This is a simply pull producer that feeds requests to the modbus client
    '''

    __tid = Defaults.TransactionId

    def __init__(self, socket):
        ''' Sets up the producer to begin sending requests
        :param socket: The client socket wrapper
        '''
        self.socket = socket

    def execute(self, request):
        ''' Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        retries = Defaults.Retries
        request.transaction_id = self.__getNextTID()
        _logging.debug("Running transaction %d" % request.transaction_id)

        while retries > 0:
            try:
                self.socket.connect()
                self.socket.send(self.framer.buildPacket(request))
                #return tr.readResponse()
            except socket.error, msg:
                self.socket.close()
                _logging.debug("Transaction failed. (%s) " % msg)
                retries -= 1

    def __getNextTID(self):
        ''' Used internally to handle the transaction identifiers.
        As the transaction identifier is represented with two
        bytes, the highest TID is 0xffff
        '''
        tid = ModbusTransactionManager.__tid
        ModbusTransactionManager.__tid = (1 +
            ModbusTransactionManager.__tid) & 0xffff
        return tid

#---------------------------------------------------------------------------#
# Client Protocols
#---------------------------------------------------------------------------#
class ModbusClientProtocol(Object):
    ''' Implements a modbus client in twisted '''

    def __init__(self, framer=ModbusTCPFramer(ClientDecoder())):
        ''' Initializes the framer module

        :param framer: The framer to use for the protocol
        '''
        self.framer = framer

    def dataReceived(self, data):
        '''
        Get response, check for valid message, decode result
        @param data The data returned from the server
        '''
        self.frame.processIncomingPacket(data, self.execute)

    def execute(self, result):
        ''' The callback to call with the resulting message
        :param request: The decoded request message
        '''
        self.factory.addResponse(result)

class ModbusTcpClient(object):
    ''' Implementation of a modbus tcp client
    '''

    def __init__(self, host, port=Defaults.Port):
        ''' Initialize a client instance
        :param host: The host to connect to
        :param port: The modbus port to connect to (default 502)
        '''
        self.host = host
        self.port = port
    
    def connect(self):
        ''' Connect to the modbus tcp server
        '''
        if self.socket: return
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(Defaults.Timeout)
            self.socket.connect((self.host, self.port))
            self.transaction = ModbusTransactionManager(self)
        except socket.error, msg:
            _logger.error('Connect to (%s, %s) failed: %s' % \
                (self.host, self.port, msg))
            self.close()
    
    def close(self):
        ''' Closes the underlying socket connection
        '''
        if self.sock:
            self.socket.close()
        self.socket = None

    def send(self, request):
        ''' Sends data on the underlying socket
        :param request: The encoded request to send
        '''
        if request:
            self.socket.send(request)

    #-----------------------------------------------------------------------#
    # with ModbusTcpClient as client:
    #-----------------------------------------------------------------------#
    def __enter__(self):
        ''' Implement the with enter block '''
        self.connect()
        if not self.socket:
            raise ConnectionException("Failed (%s:%s)" % (self.host, self.port))
        return self

    def __exit__(self, type, value, traceback):
        ''' Implement the with exit block '''
        self.close()

    #-----------------------------------------------------------------------#
    # Client methods
    #-----------------------------------------------------------------------#
    def _execute(self, request=None):
        if self.transaction:
            return self.transaction(request)
        raise ConnectionException("Client Not Connected")

class ModbusTCPTransport(ModbusTransport):
    def __init__(self, socket):
        self.socket = socket
    def setSocket(self, socket):
        self.socket = socket
    def writeMessage(self, message):
        data = message.encodeData()
        self.socket.send(
            struct.pack('>HHHBB',
            message.transaction_id,
            message.protocol_id,
            len(data)+2, 
            message.unit_id,
            message.function_code) + 
            data)
    def readResponse(self):
        data = self.socket.recv(7)
        if len(data) == 0:
            raise ModbusIOException("Remote party has closed connection.")
        if len(data) != 7:
            raise ModbusIOException(
                "Received less bytes (%d) than required." % len(data))
        transaction_id, protocol_id, data_length, unit_id \
            = struct.unpack('>HHHB', data)
        if data_length > 1:
            data = self.socket.recv(data_length - 1)
            if len(data) == 0:
                raise ModbusIOException("Remote party has closed connection.")
            if len(data) != (data_length - 1):
                raise ModbusIOException(
                    "Received less bytes (%d) than required." % len(data))
        else:
            raise ModbusIOException(
                "Wrong response packet received.")
        response = decodeModbusResponsePDU(data)
        response.transaction_id = transaction_id
        response.protocol_id = protocol_id
        response.unit_id = unit_id
        return response 
    def readRequest(self):
        data = self.socket.recv(7)
        if len(data) == 0:
            raise ModbusIOException("Remote party has closed connection.")
        if len(data) != 7:
            raise ModbusIOException(
                "Received less bytes (%d) than required." % len(data))
        transaction_id, protocol_id, data_length, unit_id \
            = struct.unpack('>HHHB', data)
        if protocol_id != DEFAULT_PROTOCOL_ID or data_length > 256:
            raise ModbusIOException("Wrong request packed received");
        if data_length > 1:
            data = self.socket.recv(data_length - 1)
            if len(data) == 0:
                raise ModbusIOException("Remote party has closed connection.")
            if len(data) != (data_length - 1):
                raise ModbusIOException(
                    "Received less bytes (%d) than required." % len(data))
        else:
            raise ModbusIOException(
                "Wrong request packet received.")
        request = decodeModbusRequestPDU(data)
        request.transaction_id = transaction_id
        request.protocol_id = protocol_id
        request.unit_id = unit_id
        return request

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ModbusMessageProducer",
    "ModbusClientProtocol", "ModbusClientFactory",
]
