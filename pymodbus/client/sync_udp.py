"""**Modbus client UDP communication.**

Example::

    from pymodbus.client import AsyncModbusUdpClient

    def run():
        client = AsyncModbusUdpClient(
            "127.0.0.1",
            # Common optional paramers:
            #    port=502,
            #    modbus_decoder=ClientDecoder,
            #    framer=ModbusSocketFramer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,
            #    strict=True,
            # UDP setup parameters
            #    source_address=("localhost", 0),
        )

        client.connect()
        ...
        client.close()
"""
import logging
import socket

from pymodbus.exceptions import ConnectionException
from pymodbus.client.base import ModbusBaseClient
from pymodbus.transaction import ModbusSocketFramer

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Modbus UDP Client Transport Implementation
# --------------------------------------------------------------------------- #


class ModbusUdpClient(ModbusBaseClient):
    r"""Modbus client for UDP communication.

    Common parameters are documented in :class:`ModbusBaseClient`

    :param host: (positional) Host IP address
    :param port: (optional default 502) The serial port used for communication.
    :param framer: (optional, default ModbusSocketFramer) Framer class.
    :param source_address: (optional, default none) source address of client,
    :param \*\*kwargs: (optional) Extra experimental parameters for transport
    :return: client object
    """

    def __init__(
        self,
        host,
        port=502,
        framer=ModbusSocketFramer,
        source_address=None,
        **kwargs,
    ):
        """Initialize Asyncio Modbus UDP Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.host = host
        self.params.port = port
        self.source_address = source_address

        self.socket = None

    @classmethod
    def _get_address_family(cls, address):
        """Get the correct address family."""
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
            family = ModbusUdpClient._get_address_family(self.params.host)
            self.socket = socket.socket(family, socket.SOCK_DGRAM)
            self.socket.settimeout(self.params.timeout)
        except socket.error as exc:
            txt = f"Unable to create udp socket {exc}"
            _logger.error(txt)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        self.socket = None

    def send(self, request):
        """Send data on the underlying socket."""
        super().send(request)
        if not self.socket:
            raise ConnectionException(str(self))
        if request:
            return self.socket.sendto(request, (self.params.host, self.params.port))
        return 0

    def recv(self, size):
        """Read data from the underlying descriptor."""
        super().recv(size)
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
        return f"ModbusUdpClient({self.params.host}:{self.params.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.params.host}, port={self.params.port}, timeout={self.params.timeout}>"
        )
