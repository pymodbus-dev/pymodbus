import socket
import serial
import time
import sys
from functools import partial
from pymodbus.constants import Defaults
from pymodbus.utilities import hexlify_packets, ModbusTransactionState
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import NotImplementedException, ParameterException
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import FifoTransactionManager
from pymodbus.transaction import DictTransactionManager
from pymodbus.transaction import ModbusSocketFramer, ModbusBinaryFramer
from pymodbus.transaction import ModbusAsciiFramer, ModbusRtuFramer
from pymodbus.client.common import ModbusClientMixin

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# The Synchronous Clients
# --------------------------------------------------------------------------- #


class BaseModbusClient(ModbusClientMixin):
    """
    Inteface for a modbus synchronous client. Defined here are all the
    methods for performing the related request methods.  Derived classes
    simply need to implement the transport methods and set the correct
    framer.
    """
    def __init__(self, framer, **kwargs):
        """ Initialize a client instance

        :param framer: The modbus framer implementation to use
        """
        self.framer = framer
        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self, **kwargs)
        else:
            self.transaction = FifoTransactionManager(self, **kwargs)
        self._debug = False
        self._debugfd = None

    # ----------------------------------------------------------------------- #
    # Client interface
    # ----------------------------------------------------------------------- #
    def connect(self):
        """ Connect to the modbus remote host

        :returns: True if connection succeeded, False otherwise
        """
        raise NotImplementedException("Method not implemented by derived class")

    def close(self):
        """ Closes the underlying socket connection
        """
        pass

    def is_socket_open(self):
        """
        Check whether the underlying socket/serial is open or not.

        :returns: True if socket/serial is open, False otherwise
        """
        raise NotImplementedException(
            "is_socket_open() not implemented by {}".format(self.__str__())
        )

    def send(self, request):
        _logger.debug("New Transaction state 'SENDING'")
        self.state = ModbusTransactionState.SENDING
        return self._send(request)

    def _send(self, request):
        """ Sends data on the underlying socket

        :param request: The encoded request to send
        :return: The number of bytes written
        """
        raise NotImplementedException("Method not implemented by derived class")

    def recv(self, size):
        return self._recv(size)

    def _recv(self, size):
        """ Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        """
        raise NotImplementedException("Method not implemented by derived class")

    # ----------------------------------------------------------------------- #
    # Modbus client methods
    # ----------------------------------------------------------------------- #
    def execute(self, request=None):
        """
        :param request: The request to process
        :returns: The result of the request execution
        """
        if not self.connect():
            raise ConnectionException("Failed to connect[%s]" % (self.__str__()))
        return self.transaction.execute(request)

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
    def __enter__(self):
        """ Implement the client with enter block

        :returns: The current instance of the client
        """
        if not self.connect():
            raise ConnectionException("Failed to connect[%s]" % (self.__str__()))
        return self

    def __exit__(self, klass, value, traceback):
        """ Implement the client with exit block """
        self.close()

    def idle_time(self):
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def debug_enabled(self):
        """
        Returns a boolean indicating if debug is enabled.
        """
        return self._debug

    def set_debug(self, debug):
        """
        Sets the current debug flag.
        """
        self._debug = debug

    def trace(self, writeable):
        if writeable:
            self.set_debug(True)
        self._debugfd = writeable

    def _dump(self, data, direction):
        fd = self._debugfd if self._debugfd else sys.stdout
        try:
            fd.write(hexlify_packets(data))
        except Exception as e:
            self._logger.debug(hexlify_packets(data))
            self._logger.exception(e)

    def __str__(self):
        """ Builds a string representation of the connection

        :returns: The string representation
        """
        return "Null Transport"


# --------------------------------------------------------------------------- #
# Modbus TCP Client Transport Implementation
# --------------------------------------------------------------------------- #
class ModbusTcpClient(BaseModbusClient):
    """ Implementation of a modbus tcp client
    """

    def __init__(self, host='127.0.0.1', port=Defaults.Port,
        framer=ModbusSocketFramer, **kwargs):
        """ Initialize a client instance

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        :param source_address: The source address tuple to bind to (default ('', 0))
        :param timeout: The timeout to use for this socket (default Defaults.Timeout)
        :param framer: The modbus framer to use (default ModbusSocketFramer)

        .. note:: The host argument will accept ipv4 and ipv6 hosts
        """
        self.host = host
        self.port = port
        self.source_address = kwargs.get('source_address', ('', 0))
        self.socket = None
        self.timeout = kwargs.get('timeout',  Defaults.Timeout)
        BaseModbusClient.__init__(self, framer(ClientDecoder(), self), **kwargs)

    def connect(self):
        """ Connect to the modbus tcp server

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket: return True
        try:
            self.socket = socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout,
                source_address=self.source_address)
        except socket.error as msg:
            _logger.error('Connection to (%s, %s) '
                          'failed: %s' % (self.host, self.port, msg))
            self.close()
        return self.socket is not None

    def close(self):
        """ Closes the underlying socket connection
        """
        if self.socket:
            self.socket.close()
        self.socket = None

    def _send(self, request):
        """ Sends data on the underlying socket

        :param request: The encoded request to send
        :return: The number of bytes written
        """
        if not self.socket:
            raise ConnectionException(self.__str__())
        if request:
            return self.socket.send(request)
        return 0

    def _recv(self, size):
        """ Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        """
        if not self.socket:
            raise ConnectionException(self.__str__())
            # socket.recv(size) waits until it gets some data from the host but
            # not necessarily the entire response that can be fragmented in
            # many packets.
            # To avoid the splitted responses to be recognized as invalid
            # messages and to be discarded, loops socket.recv until full data
            # is received or timeout is expired.
            # If timeout expires returns the read data, also if its length is
            # less than the expected size.
        self.socket.setblocking(0)
        begin = time.time()

        data = b''
        if size is not None:
            while len(data) < size:
                try:
                    data += self.socket.recv(size - len(data))
                except socket.error:
                    pass
                if not self.timeout or (time.time() - begin > self.timeout):
                    break
        else:
            while True:
                try:
                    data += self.socket.recv(1)
                except socket.error:
                    pass
                if not self.timeout or (time.time() - begin > self.timeout):
                    break
        return data

    def is_socket_open(self):
        return True if self.socket is not None else False

    def __str__(self):
        """ Builds a string representation of the connection

        :returns: The string representation
        """
        return "ModbusTcpClient(%s:%s)" % (self.host, self.port)

    def __repr__(self):
        return (
            "<{} at {} socket={self.socket}, ipaddr={self.host}, "
            "port={self.port}, timeout={self.timeout}>"
        ).format(self.__class__.__name__, hex(id(self)), self=self)



# --------------------------------------------------------------------------- #
# Modbus UDP Client Transport Implementation
# --------------------------------------------------------------------------- #
class ModbusUdpClient(BaseModbusClient):
    """ Implementation of a modbus udp client
    """

    def __init__(self, host='127.0.0.1', port=Defaults.Port,
                 framer=ModbusSocketFramer, **kwargs):
        """ Initialize a client instance

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        :param framer: The modbus framer to use (default ModbusSocketFramer)
        :param timeout: The timeout to use for this socket (default None)
        """
        self.host = host
        self.port = port
        self.socket = None
        self.timeout = kwargs.get('timeout', None)
        BaseModbusClient.__init__(self, framer(ClientDecoder(), self), **kwargs)

    @classmethod
    def _get_address_family(cls, address):
        """ A helper method to get the correct address family
        for a given address.

        :param address: The address to get the af for
        :returns: AF_INET for ipv4 and AF_INET6 for ipv6
        """
        try:
            _ = socket.inet_pton(socket.AF_INET6, address)
        except socket.error: # not a valid ipv6 address
            return socket.AF_INET
        return socket.AF_INET6

    def connect(self):
        """ Connect to the modbus tcp server

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            family = ModbusUdpClient._get_address_family(self.host)
            self.socket = socket.socket(family, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
        except socket.error as ex:
            _logger.error('Unable to create udp socket %s' % ex)
            self.close()
        return self.socket is not None

    def close(self):
        """ Closes the underlying socket connection
        """
        self.socket = None

    def _send(self, request):
        """ Sends data on the underlying socket

        :param request: The encoded request to send
        :return: The number of bytes written
        """
        if not self.socket:
            raise ConnectionException(self.__str__())
        if request:
            return self.socket.sendto(request, (self.host, self.port))
        return 0

    def _recv(self, size):
        """ Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        """
        if not self.socket:
            raise ConnectionException(self.__str__())
        return self.socket.recvfrom(size)[0]

    def is_socket_open(self):
        return True if self.socket is not None else False

    def __str__(self):
        """ Builds a string representation of the connection

        :returns: The string representation
        """
        return "ModbusUdpClient(%s:%s)" % (self.host, self.port)

    def __repr__(self):
        return (
            "<{} at {} socket={self.socket}, ipaddr={self.host}, "
            "port={self.port}, timeout={self.timeout}>"
        ).format(self.__class__.__name__, hex(id(self)), self=self)

# --------------------------------------------------------------------------- #
# Modbus Serial Client Transport Implementation
# --------------------------------------------------------------------------- #
class ModbusSerialClient(BaseModbusClient):
    """ Implementation of a modbus serial client
    """
    state = ModbusTransactionState.IDLE

    def __init__(self, method='ascii', **kwargs):
        """ Initialize a serial client instance

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
        """
        self.method = method
        self.socket = None
        BaseModbusClient.__init__(self, self.__implementation(method, self),
                                  **kwargs)

        self.port = kwargs.get('port', 0)
        self.stopbits = kwargs.get('stopbits', Defaults.Stopbits)
        self.bytesize = kwargs.get('bytesize', Defaults.Bytesize)
        self.parity = kwargs.get('parity',   Defaults.Parity)
        self.baudrate = kwargs.get('baudrate', Defaults.Baudrate)
        self.timeout = kwargs.get('timeout',  Defaults.Timeout)
        self.last_frame_end = None
        if self.method == "rtu":
            if self.baudrate > 19200:
                self.silent_interval = 1.75 / 1000  # ms
            else:
                self.silent_interval = 3.5 * (1 + 8 + 2) / self.baudrate
            self.silent_interval = round(self.silent_interval, 6)

    @staticmethod
    def __implementation(method, client):
        """ Returns the requested framer

        :method: The serial framer to instantiate
        :returns: The requested serial framer
        """
        method = method.lower()
        if method == 'ascii':
            return ModbusAsciiFramer(ClientDecoder(), client)
        elif method == 'rtu':
            return ModbusRtuFramer(ClientDecoder(), client)
        elif method == 'binary':
            return ModbusBinaryFramer(ClientDecoder(), client)
        elif method == 'socket':
            return ModbusSocketFramer(ClientDecoder(), client)
        raise ParameterException("Invalid framer method requested")

    def connect(self):
        """ Connect to the modbus serial server

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            self.socket = serial.Serial(port=self.port,
                                        timeout=self.timeout,
                                        bytesize=self.bytesize,
                                        stopbits=self.stopbits,
                                        baudrate=self.baudrate,
                                        parity=self.parity)
        except serial.SerialException as msg:
            _logger.error(msg)
            self.close()
        if self.method == "rtu":
            self.last_frame_end = None
        return self.socket is not None

    def close(self):
        """ Closes the underlying socket connection
        """
        if self.socket:
            self.socket.close()
        self.socket = None

    def _in_waiting(self):
        in_waiting = ("in_waiting" if hasattr(
            self.socket, "in_waiting") else "inWaiting")

        if in_waiting == "in_waiting":
            waitingbytes = getattr(self.socket, in_waiting)
        else:
            waitingbytes = getattr(self.socket, in_waiting)()
        return waitingbytes

    def _send(self, request):
        """ Sends data on the underlying socket

        If receive buffer still holds some data then flush it.

        Sleep if last send finished less than 3.5 character
        times ago.

        :param request: The encoded request to send
        :return: The number of bytes written
        """
        if not self.socket:
            raise ConnectionException(self.__str__())
        if request:
            try:
                waitingbytes = self._in_waiting()
                if waitingbytes:
                    result = self.socket.read(waitingbytes)
                    if _logger.isEnabledFor(logging.WARNING):
                        _logger.warning("Cleanup recv buffer before "
                                        "send: " + hexlify_packets(result))
            except NotImplementedError:
                pass

            size = self.socket.write(request)
            return size
        return 0

    def _wait_for_data(self):
        if self.timeout is not None and self.timeout != 0:
            condition = partial(lambda start, timeout: (time.time() - start) <= timeout, timeout=self.timeout)
        else:
            condition = partial(lambda dummy1, dummy2: True, dummy2=None)
        start = time.time()
        while condition(start):
            size = self._in_waiting()
            if size:
                break
            time.sleep(0.01)
        return size

    def _recv(self, size):
        """ Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read
        """
        if not self.socket:
            raise ConnectionException(self.__str__())
        if size is None:
            size = self._wait_for_data()
        result = self.socket.read(size)
        return result

    def is_socket_open(self):
        if self.socket:
            if hasattr(self.socket, "is_open"):
                return self.socket.is_open
            else:
                return self.socket.isOpen()
        return False

    def __str__(self):
        """ Builds a string representation of the connection

        :returns: The string representation
        """
        return "ModbusSerialClient(%s baud[%s])" % (self.method, self.baudrate)

    def __repr__(self):
        return (
            "<{} at {} socket={self.socket}, method={self.method}, "
            "timeout={self.timeout}>"
        ).format(self.__class__.__name__, hex(id(self)), self=self)

# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = [
    "ModbusTcpClient", "ModbusUdpClient", "ModbusSerialClient"
]
