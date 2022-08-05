"""Sync client."""
# pylint: disable=missing-type-doc
import logging
import socket
import sys

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
# Modbus UDP Client Transport Implementation
# --------------------------------------------------------------------------- #


class ModbusUdpClient(BaseModbusClient):
    """Implementation of a modbus udp client."""

    def __init__(
        self, host="127.0.0.1", port=Defaults.Port, framer=ModbusSocketFramer, **kwargs
    ):
        """Initialize a client instance.

        :param host: The host to connect to (default 127.0.0.1)
        :param port: The modbus port to connect to (default 502)
        :param framer: The modbus framer to use (default ModbusSocketFramer)
        :param timeout: The timeout to use for this socket (default None)
        """
        self.host = host
        self.port = port
        self.socket = None
        self.timeout = kwargs.get("timeout", None)
        BaseModbusClient.__init__(self, framer(ClientDecoder(), self), **kwargs)

    @classmethod
    def _get_address_family(cls, address):
        """Get the correct address family.

        for a given address.

        :param address: The address to get the af for
        :returns: AF_INET for ipv4 and AF_INET6 for ipv6
        """
        try:
            _ = socket.inet_pton(socket.AF_INET6, address)
        except socket.error:  # not a valid ipv6 address
            return socket.AF_INET
        return socket.AF_INET6

    def connect(self):
        """Connect to the modbus tcp server.

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            family = ModbusUdpClient._get_address_family(self.host)
            self.socket = socket.socket(family, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
        except socket.error as exc:
            txt = f"Unable to create udp socket {exc}"
            _logger.error(txt)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        self.socket = None

    def _send(self, request):
        """Send data on the underlying socket.

        :param request: The encoded request to send
        :return: The number of bytes written
        :raises ConnectionException:
        """
        if not self.socket:
            raise ConnectionException(str(self))
        if request:
            return self.socket.sendto(request, (self.host, self.port))
        return 0

    def _recv(self, size):
        """Read data from the underlying descriptor.

        :param size: The number of bytes to read
        :return: The bytes read
        :raises ConnectionException:
        """
        if not self.socket:
            raise ConnectionException(str(self))
        return self.socket.recvfrom(size)[0]

    def is_socket_open(self):
        """Check if socket is open."""
        if self.socket:
            return True
        return self.connect()

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"ModbusUdpClient({self.host}:{self.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.host}, port={self.port}, timeout={self.timeout}>"
        )
