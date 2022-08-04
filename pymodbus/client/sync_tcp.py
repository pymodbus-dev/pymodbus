"""Sync client."""
# pylint: disable=missing-type-doc
import logging
import select
import socket
import sys
import time

from pymodbus.client.helper_sync import ModbusClientMixin
from pymodbus.constants import Defaults
from pymodbus.exceptions import (
    ConnectionException,
    NotImplementedException,
)
from pymodbus.factory import ClientDecoder
from pymodbus.transaction import (
    DictTransactionManager,
    ModbusSocketFramer,
)
from pymodbus.utilities import ModbusTransactionState, hexlify_packets

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# The Synchronous Clients
# --------------------------------------------------------------------------- #


class BaseModbusClient(ModbusClientMixin):
    """Interface for a modbus synchronous client.

    Defined here are all the methods for performing the related
    request methods.
    Derived classes simply need to implement the transport methods and set the correct
    framer.
    """

    def __init__(self, framer, **kwargs):
        """Initialize a client instance.

        :param framer: The modbus framer implementation to use
        """
        self.framer = framer
        self.transaction = DictTransactionManager(self, **kwargs)
        self._debug = False
        self._debugfd = None
        self.broadcast_enable = kwargs.get(
            "broadcast_enable", Defaults.broadcast_enable
        )

    # ----------------------------------------------------------------------- #
    # Client interface
    # ----------------------------------------------------------------------- #
    def connect(self):
        """Connect to the modbus remote host.

        :raises NotImplementedException:
        """
        raise NotImplementedException("Method not implemented by derived class")

    def close(self):
        """Close the underlying socket connection."""

    def is_socket_open(self):
        """Check whether the underlying socket/serial is open or not.

        :raises NotImplementedException:
        """
        raise NotImplementedException(
            f"is_socket_open() not implemented by {self.__str__()}"  # pylint: disable=unnecessary-dunder-call
        )

    def send(self, request):
        """Send request."""
        if self.state != ModbusTransactionState.RETRYING:
            _logger.debug('New Transaction state "SENDING"')
            self.state = ModbusTransactionState.SENDING
        return self._send(request)

    def _send(self, request):
        """Send data on the underlying socket.

        :param request: The encoded request to send
        :raises NotImplementedException:
        """
        raise NotImplementedException("Method not implemented by derived class")

    def recv(self, size):
        """Receive data."""
        return self._recv(size)

    def _recv(self, size):
        """Read data from the underlying descriptor.

        :param size: The number of bytes to read
        :raises NotImplementedException:
        """
        raise NotImplementedException("Method not implemented by derived class")

    # ----------------------------------------------------------------------- #
    # Modbus client methods
    # ----------------------------------------------------------------------- #
    def execute(self, request=None):
        """Execute.

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException:
        """
        if not self.connect():
            raise ConnectionException(f"Failed to connect[{str(self)}]")
        return self.transaction.execute(request)

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
    def __enter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """
        if not self.connect():
            raise ConnectionException(f"Failed to connect[{self.__str__()}]")
        return self

    def __exit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        self.close()

    def idle_time(self):
        """Bus Idle Time to initiate next transaction

        :return: time stamp
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def debug_enabled(self):
        """Return a boolean indicating if debug is enabled."""
        return self._debug

    def set_debug(self, debug):
        """Set the current debug flag."""
        self._debug = debug

    def trace(self, writeable):
        """Show trace."""
        if writeable:
            self.set_debug(True)
        self._debugfd = writeable

    def _dump(self, data):
        """Dump."""
        fd = self._debugfd if self._debugfd else sys.stdout
        try:
            fd.write(hexlify_packets(data))
        except Exception as exc:  # pylint: disable=broad-except
            _logger.debug(hexlify_packets(data))
            _logger.exception(exc)

    def register(self, function):
        """Register a function and sub function class with the decoder.

        :param function: Custom function class to register
        """
        self.framer.decoder.register(function)

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return "Null Transport"


# --------------------------------------------------------------------------- #
# Modbus TCP Client Transport Implementation
# --------------------------------------------------------------------------- #
class ModbusTcpClient(BaseModbusClient):
    """Implementation of a modbus tcp client."""

    def __init__(
        self, host="127.0.0.1", port=Defaults.Port, framer=ModbusSocketFramer, **kwargs
    ):
        """Initialize a client instance.

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        :param source_address: The source address tuple to bind to (default ("", 0))
        :param timeout: The timeout to use for this socket (default Defaults.Timeout)
        :param framer: The modbus framer to use (default ModbusSocketFramer)

        .. note:: The host argument will accept ipv4 and ipv6 hosts
        """
        self.host = host
        self.port = port
        self.source_address = kwargs.get("source_address", ("", 0))
        self.socket = None
        self.timeout = kwargs.get("timeout", Defaults.Timeout)
        BaseModbusClient.__init__(self, framer(ClientDecoder(), self), **kwargs)

    def connect(self):
        """Connect to the modbus tcp server.

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            self.socket = socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout,
                source_address=self.source_address,
            )
            txt = f"Connection to Modbus server established. Socket {self.socket.getsockname()}"
            _logger.debug(txt)
        except socket.error as msg:
            txt = f"Connection to ({self.host}, {self.port}) failed: {msg}"
            _logger.error(txt)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def _check_read_buffer(self):
        """Check read buffer."""
        time_ = time.time()
        end = time_ + self.timeout
        data = None
        ready = select.select([self.socket], [], [], end - time_)
        if ready[0]:
            data = self.socket.recv(1024)
        return data

    def _send(self, request):
        """Send data on the underlying socket.

        :param request: The encoded request to send
        :return: The number of bytes written
        :raises ConnectionException:
        """
        if not self.socket:
            raise ConnectionException(str(self))
        if self.state == ModbusTransactionState.RETRYING:
            if data := self._check_read_buffer():
                return data

        if request:
            return self.socket.send(request)
        return 0

    def _recv(self, size):
        """Read data from the underlying descriptor.

        :param size: The number of bytes to read
        :return: The bytes read if the peer sent a response, or a zero-length
                 response if no data packets were received from the client at
                 all.
        :raises ConnectionException:
        """
        if not self.socket:
            raise ConnectionException(str(self))

        # socket.recv(size) waits until it gets some data from the host but
        # not necessarily the entire response that can be fragmented in
        # many packets.
        # To avoid split responses to be recognized as invalid
        # messages and to be discarded, loops socket.recv until full data
        # is received or timeout is expired.
        # If timeout expires returns the read data, also if its length is
        # less than the expected size.
        self.socket.setblocking(0)

        timeout = self.timeout

        # If size isn"t specified read up to 4096 bytes at a time.
        if size is None:
            recv_size = 4096
        else:
            recv_size = size

        data = []
        data_length = 0
        time_ = time.time()
        end = time_ + timeout
        while recv_size > 0:
            try:
                ready = select.select([self.socket], [], [], end - time_)
            except ValueError:
                return self._handle_abrupt_socket_close(size, data, time.time() - time_)
            if ready[0]:
                if (recv_data := self.socket.recv(recv_size)) == b"":
                    return self._handle_abrupt_socket_close(
                        size, data, time.time() - time_
                    )
                data.append(recv_data)
                data_length += len(recv_data)
            time_ = time.time()

            # If size isn"t specified continue to read until timeout expires.
            if size:
                recv_size = size - data_length

            # Timeout is reduced also if some data has been received in order
            # to avoid infinite loops when there isn"t an expected response
            # size and the slave sends noisy data continuously.
            if time_ > end:
                break

        return b"".join(data)

    def _handle_abrupt_socket_close(self, size, data, duration):
        """Handle unexpected socket close by remote end.

        Intended to be invoked after determining that the remote end
        has unexpectedly closed the connection, to clean up and handle
        the situation appropriately.

        :param size: The number of bytes that was attempted to read
        :param data: The actual data returned
        :param duration: Duration from the read was first attempted
               until it was determined that the remote closed the
               socket
        :return: The more than zero bytes read from the remote end
        :raises ConnectionException: If the remote end didn't send any
                 data at all before closing the connection.
        """
        self.close()
        size_txt = size if size else "unbounded read"
        readsize = f"read of {size_txt} bytes"
        msg = (
            f"{self}: Connection unexpectedly closed "
            f"{duration} seconds into {readsize}"
        )
        if data:
            result = b"".join(data)
            msg += f" after returning {len(result)} bytes"
            _logger.warning(msg)
            return result
        msg += " without response from unit before it closed connection"
        raise ConnectionException(msg)

    def is_socket_open(self):
        """Check if socket is open."""
        return self.socket is not None

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"ModbusTcpClient({self.host}:{self.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.host}, port={self.port}, timeout={self.timeout}>"
        )
