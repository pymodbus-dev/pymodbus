"""Sync client."""
# pylint: disable=missing-type-doc
import logging
import socket
import time

from pymodbus.client.helper_tls import sslctx_provider
from pymodbus.client.sync_tcp import ModbusTcpClient
from pymodbus.constants import Defaults
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusTlsFramer

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Modbus TLS Client Transport Implementation
# --------------------------------------------------------------------------- #


class ModbusTlsClient(ModbusTcpClient):
    """Implementation of a modbus tls client."""

    def __init__(
        self,
        host="localhost",
        port=Defaults.TLSPort,
        sslctx=None,
        certfile=None,
        keyfile=None,
        password=None,
        framer=ModbusTlsFramer,
        **kwargs,
    ):
        """Initialize a client instance.

        :param host: The host to connect to (default localhost)
        :param port: The modbus port to connect to (default 802)
        :param sslctx: The SSLContext to use for TLS (default None and auto create)
        :param certfile: The optional client"s cert file path for TLS server request
        :param keyfile: The optional client"s key file path for TLS server request
        :param password: The password for for decrypting client"s private key file
        :param source_address: The source address tuple to bind to (default ("", 0))
        :param timeout: The timeout to use for this socket (default Defaults.Timeout)
        :param framer: The modbus framer to use (default ModbusSocketFramer)

        .. note:: The host argument will accept ipv4 and ipv6 hosts
        """
        self.sslctx = sslctx_provider(sslctx, certfile, keyfile, password)
        ModbusTcpClient.__init__(self, host, port, framer, **kwargs)

    def connect(self):
        """Connect to the modbus tls server.

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(self.source_address)
            self.socket = self.sslctx.wrap_socket(
                sock, server_side=False, server_hostname=self.host
            )
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
        except socket.error as msg:
            txt = f"Connection to ({self.host}, {self.port}) failed: {msg}"
            _logger.error(txt)
            self.close()
        return self.socket is not None

    def _recv(self, size):
        """Read data from the underlying descriptor.

        :param size: The number of bytes to read
        :return: The bytes read
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
        timeout = self.timeout

        # If size isn"t specified read 1 byte at a time.
        if size is None:
            recv_size = 1
        else:
            recv_size = size

        data = b""
        time_ = time.time()
        end = time_ + timeout
        while recv_size > 0:
            data += self.socket.recv(recv_size)
            time_ = time.time()

            # If size isn"t specified continue to read until timeout expires.
            if size:
                recv_size = size - len(data)

            # Timeout is reduced also if some data has been received in order
            # to avoid infinite loops when there isn"t an expected response
            # size and the slave sends noisy data continuously.
            if time_ > end:
                break

        return data

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"ModbusTlsClient({self.host}:{self.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.host}, port={self.port}, sslctx={self.sslctx}, "
            f"timeout={self.timeout}>"
        )
