import socket
import serial

from pymodbus.constants import Defaults
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import NotImplementedException, ParameterException
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import FifoTransactionManager
from pymodbus.transaction import DictTransactionManager
from pymodbus.transaction import ModbusSocketFramer, ModbusBinaryFramer
from pymodbus.transaction import ModbusAsciiFramer, ModbusRtuFramer
from pymodbus.client.common import ModbusClientMixin

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)


#---------------------------------------------------------------------------#
# The Synchronous Clients
#---------------------------------------------------------------------------#
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
        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self)
        else: self.transaction = FifoTransactionManager(self)

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
        pass

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
        if not self.connect():
            raise ConnectionException("Failed to connect[%s]" % (self.__str__()))
        return self.transaction.execute(request)

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

    def __exit__(self, klass, value, traceback):
        ''' Implement the client with exit block '''
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

    def __init__(self, host='127.0.0.1', port=Defaults.Port, framer=ModbusSocketFramer):
        ''' Initialize a client instance

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        :param framer: The modbus framer to use (default ModbusSocketFramer)

        .. note:: The host argument will accept ipv4 and ipv6 hosts
        '''
        self.host = host
        self.port = port
        self.socket = None
        BaseModbusClient.__init__(self, framer(ClientDecoder()))

    def connect(self):
        ''' Connect to the modbus tcp server

        :returns: True if connection succeeded, False otherwise
        '''
        if self.socket: return True
        try:
            self.socket = socket.create_connection((self.host, self.port), Defaults.Timeout)
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
        if not self.socket:
            raise ConnectionException(self.__str__())
        if request:
            return self.socket.send(request)
        return 0

    def _recv(self, size):
        ''' Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        '''
        if not self.socket:
            raise ConnectionException(self.__str__())
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

    def __init__(self, host='127.0.0.1', port=Defaults.Port, framer=ModbusSocketFramer):
        ''' Initialize a client instance

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        :param framer: The modbus framer to use (default ModbusSocketFramer)
        '''
        self.host = host
        self.port = port
        self.socket = None
        BaseModbusClient.__init__(self, framer(ClientDecoder()))

    @classmethod
    def _get_address_family(cls, address):
        ''' A helper method to get the correct address family
        for a given address.

        :param address: The address to get the af for
        :returns: AF_INET for ipv4 and AF_INET6 for ipv6
        '''
        try:
            _ = socket.inet_pton(socket.AF_INET6, address)
        except socket.error: # not a valid ipv6 address
            return socket.AF_INET
        return socket.AF_INET6

    def connect(self):
        ''' Connect to the modbus tcp server

        :returns: True if connection succeeded, False otherwise
        '''
        if self.socket: return True
        try:
            family = ModbusUdpClient._get_address_family(self.host)
            self.socket = socket.socket(family, socket.SOCK_DGRAM)
        except socket.error, ex:
            _logger.error('Unable to create udp socket %s' % ex)
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
        if not self.socket:
            raise ConnectionException(self.__str__())
        if request:
            return self.socket.sendto(request, (self.host, self.port))
        return 0

    def _recv(self, size):
        ''' Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        '''
        if not self.socket:
            raise ConnectionException(self.__str__())
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
    ''' Implementation of a modbus serial client
    '''

    def __init__(self, method='ascii', **kwargs):
        ''' Initialize a serial client instance

        The methods to connect are::

          - ascii
          - rtu
          - binary

        :param method: The method to use for connection
        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout between serial requests (default 3s)
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
        elif method == 'socket': return ModbusSocketFramer(ClientDecoder())
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
        if not self.socket:
            raise ConnectionException(self.__str__())
        if request:
            return self.socket.write(request)
        return 0

    def _recv(self, size):
        ''' Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        '''
        if not self.socket:
            raise ConnectionException(self.__str__())
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
