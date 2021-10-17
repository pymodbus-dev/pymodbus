import socket
import select
import serial
import time
import ssl
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
from pymodbus.transaction import ModbusTlsFramer
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
        self.transaction = DictTransactionManager(self, **kwargs)
        self._debug = False
        self._debugfd = None
        self.broadcast_enable = kwargs.get('broadcast_enable', Defaults.broadcast_enable)

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
        if self.state != ModbusTransactionState.RETRYING:
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
        """
        Bus Idle Time to initiate next transaction
        :return: time stamp
        """
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
            _logger.debug(hexlify_packets(data))
            _logger.exception(e)

    def register(self, function):
        """
        Registers a function and sub function class with the decoder
        :param function: Custom function class to register
        :return:
        """
        self.framer.decoder.register(function)

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
        if self.socket:
            return True
        try:
            self.socket = socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout,
                source_address=self.source_address)
            _logger.debug("Connection to Modbus server established. "
                          "Socket {}".format(self.socket.getsockname()))
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

    def _check_read_buffer(self, recv_size=None):
        time_ = time.time()
        end = time_ + self.timeout
        data = None
        ready = select.select([self.socket], [], [], end - time_)
        if ready[0]:
            data = self.socket.recv(1024)
        return data

    def _send(self, request):
        """ Sends data on the underlying socket

        :param request: The encoded request to send
        :return: The number of bytes written
        """
        if not self.socket:
            raise ConnectionException(self.__str__())
        if self.state == ModbusTransactionState.RETRYING:
            data = self._check_read_buffer()
            if data:
                return data

        if request:
            return self.socket.send(request)
        return 0

    def _recv(self, size):
        """ Reads data from the underlying descriptor

        :param size: The number of bytes to read
        :return: The bytes read if the peer sent a response, or a zero-length
                 response if no data packets were received from the client at
                 all.
        :raises: ConnectionException if the socket is not initialized, or the
                 peer either has closed the connection before this method is
                 invoked or closes it before sending any data before timeout.
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

        timeout = self.timeout

        # If size isn't specified read up to 4096 bytes at a time.
        if size is None:
            recv_size = 4096
        else:
            recv_size = size

        data = []
        data_length = 0
        time_ = time.time()
        end = time_ + timeout
        while recv_size > 0:
            ready = select.select([self.socket], [], [], end - time_)
            if ready[0]:
                recv_data = self.socket.recv(recv_size)
                if recv_data == b'':
                    return self._handle_abrupt_socket_close(
                        size, data, time.time() - time_)
                data.append(recv_data)
                data_length += len(recv_data)
            time_ = time.time()

            # If size isn't specified continue to read until timeout expires.
            if size:
                recv_size = size - data_length

            # Timeout is reduced also if some data has been received in order
            # to avoid infinite loops when there isn't an expected response
            # size and the slave sends noisy data continuously.
            if time_ > end:
                break

        return b"".join(data)

    def _handle_abrupt_socket_close(self, size, data, duration):
        """ Handle unexpected socket close by remote end

        Intended to be invoked after determining that the remote end
        has unexpectedly closed the connection, to clean up and handle
        the situation appropriately.

        :param size: The number of bytes that was attempted to read
        :param data: The actual data returned
        :param duration: Duration from the read was first attempted
               until it was determined that the remote closed the
               socket
        :return: The more than zero bytes read from the remote end
        :raises: ConnectionException If the remote end didn't send any
                 data at all before closing the connection.
        """
        self.close()
        readsize = ("read of %s bytes" % size if size
                    else "unbounded read")
        msg = ("%s: Connection unexpectedly closed "
               "%.6f seconds into %s" % (self, duration, readsize))
        if data:
            result = b"".join(data)
            msg += " after returning %s bytes" % len(result)
            _logger.warning(msg)
            return result
        msg += " without response from unit before it closed connection"
        raise ConnectionException(msg)

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
# Modbus TLS Client Transport Implementation
# --------------------------------------------------------------------------- #


class ModbusTlsClient(ModbusTcpClient):
    """ Implementation of a modbus tls client
    """

    def __init__(self, host='localhost', port=Defaults.TLSPort, sslctx=None,
        framer=ModbusTlsFramer, **kwargs):
        """ Initialize a client instance

        :param host: The host to connect to (default localhost)
        :param port: The modbus port to connect to (default 802)
        :param sslctx: The SSLContext to use for TLS (default None and auto create)
        :param source_address: The source address tuple to bind to (default ('', 0))
        :param timeout: The timeout to use for this socket (default Defaults.Timeout)
        :param framer: The modbus framer to use (default ModbusSocketFramer)

        .. note:: The host argument will accept ipv4 and ipv6 hosts
        """
        self.sslctx = sslctx
        if self.sslctx is None:
            self.sslctx = ssl.create_default_context()
            # According to MODBUS/TCP Security Protocol Specification, it is
            # TLSv2 at least
            self.sslctx.options |= ssl.OP_NO_TLSv1_1
            self.sslctx.options |= ssl.OP_NO_TLSv1
            self.sslctx.options |= ssl.OP_NO_SSLv3
            self.sslctx.options |= ssl.OP_NO_SSLv2
        ModbusTcpClient.__init__(self, host, port, framer, **kwargs)

    def connect(self):
        """ Connect to the modbus tls server

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket: return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(self.source_address)
            self.socket = self.sslctx.wrap_socket(sock, server_side=False,
                                                  server_hostname=self.host)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
        except socket.error as msg:
            _logger.error('Connection to (%s, %s) '
                          'failed: %s' % (self.host, self.port, msg))
            self.close()
        return self.socket is not None

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
        timeout = self.timeout

        # If size isn't specified read 1 byte at a time.
        if size is None:
            recv_size = 1
        else:
            recv_size = size

        data = b''
        time_ = time.time()
        end = time_ + timeout
        while recv_size > 0:
            data += self.socket.recv(recv_size)
            time_ = time.time()

            # If size isn't specified continue to read until timeout expires.
            if size:
                recv_size = size - len(data)

            # Timeout is reduced also if some data has been received in order
            # to avoid infinite loops when there isn't an expected response
            # size and the slave sends noisy data continuously.
            if time_ > end:
                break

        return data

    def __str__(self):
        """ Builds a string representation of the connection

        :returns: The string representation
        """
        return "ModbusTlsClient(%s:%s)" % (self.host, self.port)

    def __repr__(self):
        return (
            "<{} at {} socket={self.socket}, ipaddr={self.host}, "
            "port={self.port}, sslctx={self.sslctx}, timeout={self.timeout}>"
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
        if self.socket:
            return True
        return self.connect()

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
    inter_char_timeout = 0
    silent_interval = 0

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
        :param strict:  Use Inter char timeout for baudrates <= 19200 (adhere
        to modbus standards)
        :param handle_local_echo: Handle local echo of the USB-to-RS485 adaptor
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
        self._strict = kwargs.get("strict", False)
        self.last_frame_end = None
        self.handle_local_echo = kwargs.get("handle_local_echo", False)
        if self.method == "rtu":
            if self.baudrate > 19200:
                self.silent_interval = 1.75 / 1000  # ms
            else:
                self._t0 = float((1 + 8 + 2)) / self.baudrate
                self.inter_char_timeout = 1.5 * self._t0
                self.silent_interval = 3.5 * self._t0
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
        import serial
        if self.socket:
            return True
        try:
            self.socket = serial.serial_for_url(self.port,
                                        timeout=self.timeout,
                                        bytesize=self.bytesize,
                                        stopbits=self.stopbits,
                                        baudrate=self.baudrate,
                                        parity=self.parity)
            if self.method == "rtu":
                if self._strict:
                    self.socket.interCharTimeout = self.inter_char_timeout
                self.last_frame_end = None
        except serial.SerialException as msg:
            _logger.error(msg)
            self.close()
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
                    if self.state == ModbusTransactionState.RETRYING:
                        _logger.debug("Sending available data in recv "
                                      "buffer {}".format(
                            hexlify_packets(result)))
                        return result
                    if _logger.isEnabledFor(logging.WARNING):
                        _logger.warning("Cleanup recv buffer before "
                                        "send: " + hexlify_packets(result))
            except NotImplementedError:
                pass
            if self.state != ModbusTransactionState.SENDING:
                _logger.debug("New Transaction state 'SENDING'")
                self.state = ModbusTransactionState.SENDING
            size = self.socket.write(request)
            return size
        return 0

    def _wait_for_data(self):
        size = 0
        more_data = False
        if self.timeout is not None and self.timeout != 0:
            condition = partial(lambda start, timeout:
                                (time.time() - start) <= timeout,
                                timeout=self.timeout)
        else:
            condition = partial(lambda dummy1, dummy2: True, dummy2=None)
        start = time.time()
        while condition(start):
            avaialble = self._in_waiting()
            if (more_data and not avaialble) or (more_data and avaialble == size):
                break
            if avaialble and avaialble != size:
                more_data = True
                size = avaialble
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
    "ModbusTcpClient", "ModbusTlsClient", "ModbusUdpClient", "ModbusSerialClient"
]
