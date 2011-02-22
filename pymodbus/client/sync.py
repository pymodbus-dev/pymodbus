import socket
import struct
import serial

from pymodbus.constants import Defaults
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import *
from pymodbus.transaction import *
from pymodbus.client.common import ModbusClientMixin

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Client Producer/Consumer
#---------------------------------------------------------------------------#
class ModbusTransactionManager:
    '''
    This is a simply pull producer that feeds requests to the modbus client
    '''

    __tid = Defaults.TransactionId

    def __init__(self, client):
        ''' Sets up the producer to begin sending requests

        :param client: The client socket wrapper
        '''
        self.client = client

    def execute(self, request):
        ''' Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        self.response = None
        retries = Defaults.Retries
        request.transaction_id = self.__getNextTID()
        _logger.debug("Running transaction %d" % request.transaction_id)

        while retries > 0:
            try:
                self.client.connect()
                self.client._send(self.client.framer.buildPacket(request))
                # I need to fix this to read the header and the result size,
                # as this may not read the full result set, but right now
                # it should be fine...
                result = self.client._recv(1024)
                self.client.framer.processIncomingPacket(result, self.__set_result)
                break;
            except socket.error, msg:
                self.client.close()
                _logger.debug("Transaction failed. (%s) " % msg)
                retries -= 1
        return self.response

    def __set_result(self, message):
        ''' Quick helper that lets me reuse the async framer

        :param message: The decoded message
        '''
        self.response = message

    def __getNextTID(self):
        ''' Used internally to handle the transaction identifiers.
        As the transaction identifier is represented with two
        bytes, the highest TID is 0xffff
        '''
        tid = (ModbusTransactionManager.__tid + 1) & 0xffff
        ModbusTransactionManager.__tid = tid
        return tid

class BaseModbusClient(ModbusClientMixin):
    '''
    Inteface for a modbus synchronous client. Defined here are all the
    methods for performing the related request methods.  Derived classes
    simply need to implement the transport methods and set the correct
    framer.
    '''

    def __init__(self, framer):
        ''' Initialize a client instance

        :param framer: The modbus framer implementation to use
        '''
        self.framer = framer
        self.transaction = ModbusTransactionManager(self)

    #-----------------------------------------------------------------------#
    # Client interface
    #-----------------------------------------------------------------------#
    def connect(self):
        ''' Connect to the modbus remote host

        :returns: True if connection succeeded, False otherwise
        '''
        raise NotImplementedException("Method not implemented by derived class")
    
    def close(self):
        ''' Closes the underlying socket connection
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def _send(self, request):
        ''' Sends data on the underlying socket

        :param request: The encoded request to send
        :return: The number of bytes written
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def _recv(self, size):
        ''' Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        '''
        raise NotImplementedException("Method not implemented by derived class")

    #-----------------------------------------------------------------------#
    # Modbus client methods
    #-----------------------------------------------------------------------#
    def execute(self, request=None):
        '''
        :param request: The request to process
        :returns: The result of the request execution
        '''
        if self.transaction:
            return self.transaction.execute(request)
        raise ConnectionException("Client Not Connected")

    #-----------------------------------------------------------------------#
    # The magic methods
    #-----------------------------------------------------------------------#
    def __enter__(self):
        ''' Implement the client with enter block

        :returns: The current instance of the client
        '''
        if not self.connect():
            raise ConnectionException("Failed to connect[%s]" % (self.__str__()))
        return self

    def __exit__(self, type, value, traceback):
        ''' Implement the client with exit block '''
        self.close()

    def __del__(self):
        ''' Class destructor '''
        self.close()

    def __str__(self):
        ''' Builds a string representation of the connection
        
        :returns: The string representation
        '''
        return "Null Transport"

#---------------------------------------------------------------------------#
# Modbus TCP Client Transport Implementation
#---------------------------------------------------------------------------#
class ModbusTcpClient(BaseModbusClient):
    ''' Implementation of a modbus tcp client
    '''

    def __init__(self, host='127.0.0.1', port=Defaults.Port):
        ''' Initialize a client instance

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        '''
        self.host = host
        self.port = port
        self.socket = None
        BaseModbusClient.__init__(self, ModbusSocketFramer(ClientDecoder()))
    
    def connect(self):
        ''' Connect to the modbus tcp server
        
        :returns: True if connection succeeded, False otherwise
        '''
        if self.socket: return True
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(Defaults.Timeout)
            self.socket.connect((self.host, self.port))
            self.transaction = ModbusTransactionManager(self)
        except socket.error, msg:
            _logger.error('Connection to (%s, %s) failed: %s' % \
                (self.host, self.port, msg))
            self.close()
        return self.socket != None
    
    def close(self):
        ''' Closes the underlying socket connection
        '''
        if self.socket:
            self.socket.close()
        self.socket = None

    def _send(self, request):
        ''' Sends data on the underlying socket

        :param request: The encoded request to send
        :return: The number of bytes written
        '''
        if request:
            return self.socket.send(request)
        return 0

    def _recv(self, size):
        ''' Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        '''
        return self.socket.recv(size)

    def __str__(self):
        ''' Builds a string representation of the connection
        
        :returns: The string representation
        '''
        return "%s:%s" % (self.host, self.port)

#---------------------------------------------------------------------------#
# Modbus UDP Client Transport Implementation
#---------------------------------------------------------------------------#
class ModbusUdpClient(BaseModbusClient):
    ''' Implementation of a modbus udp client
    '''

    def __init__(self, host='127.0.0.1', port=Defaults.Port):
        ''' Initialize a client instance

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        '''
        self.host = host
        self.port = port
        self.socket = None
        BaseModbusClient.__init__(self, ModbusSocketFramer(ClientDecoder()))
    
    def connect(self):
        ''' Connect to the modbus tcp server

        :returns: True if connection succeeded, False otherwise
        '''
        if self.socket: return True
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #self.socket.bind(('localhost', Defaults.Port))
        except socket.error, msg:
            _logger.error('Unable to create udp socket')
            self.close()
        return self.socket != None
    
    def close(self):
        ''' Closes the underlying socket connection
        '''
        self.socket = None

    def _send(self, request):
        ''' Sends data on the underlying socket

        :param request: The encoded request to send
        :return: The number of bytes written
        '''
        if request:
            return self.socket.sendto(request, (self.host, self.port))
        return 0

    def _recv(self, size):
        ''' Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        '''
        return self.socket.recvfrom(size)[0]

    def __str__(self):
        ''' Builds a string representation of the connection
        
        :returns: The string representation
        '''
        return "%s:%s" % (self.host, self.port)

#---------------------------------------------------------------------------#
# Modbus Serial Client Transport Implementation
#---------------------------------------------------------------------------#
class ModbusSerialClient(BaseModbusClient):
    ''' Implementation of a modbus udp client
    '''

    def __init__(self, method='ascii', **kwargs):
        ''' Initialize a serial client instance

        The methods to connect are::

          - ascii
          - rtu
          - binary

        :param method: The method to use for connection
        '''
        self.method   = method
        self.socket   = None
        BaseModbusClient.__init__(self, self.__implementation(method))

        self.port     = kwargs.get('port', 0)
        self.stopbits = kwargs.get('stopbits', Defaults.Stopbits)
        self.bytesize = kwargs.get('bytesize', Defaults.Bytesize)
        self.parity   = kwargs.get('parity',   Defaults.Parity)
        self.baudrate = kwargs.get('baudrate', Defaults.Baudrate)
        self.timeout  = kwargs.get('timeout',  Defaults.Timeout)

    @staticmethod
    def __implementation(method):
        ''' Returns the requested framer

        :method: The serial framer to instantiate
        :returns: The requested serial framer
        '''
        method = method.lower()
        if   method == 'ascii':  return ModbusAsciiFramer(ClientDecoder())
        elif method == 'rtu':    return ModbusRtuFramer(ClientDecoder())
        elif method == 'binary': return ModbusBinaryFramer(ClientDecoder())
        raise ParameterException("Invalid framer method requested")
    
    def connect(self):
        ''' Connect to the modbus tcp server

        :returns: True if connection succeeded, False otherwise
        '''
        if self.socket: return True
        try:
            self.socket = serial.Serial(port=self.port, timeout=self.timeout, 
                bytesize=self.bytesize, stopbits=self.stopbits,
                baudrate=self.baudrate, parity=self.parity)
        except serial.SerialException, msg:
            _logger.error(msg)
            self.close()
        return self.socket != None
    
    def close(self):
        ''' Closes the underlying socket connection
        '''
        if self.socket:
            self.socket.close()
        self.socket = None

    def _send(self, request):
        ''' Sends data on the underlying socket

        :param request: The encoded request to send
        :return: The number of bytes written
        '''
        if request:
            return self.socket.write(request)
        return 0

    def _recv(self, size):
        ''' Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        '''
        return self.socket.read(size)

    def __str__(self):
        ''' Builds a string representation of the connection
        
        :returns: The string representation
        '''
        return "%s baud[%s]" % (self.method, self.baudrate)

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ModbusTcpClient", "ModbusUdpClient", "ModbusSerialClient"
]
