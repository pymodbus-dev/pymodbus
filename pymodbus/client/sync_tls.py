"""Modbus client TLS communication.

Example::

    from pymodbus.client import ModbusTlsClient

    def run():
        client = ModbusTlsClient(
            "localhost",
            #    port=802,
            # Common optional paramers:
            #    modbus_decoder=ClientDecoder,
            #    framer=ModbusTLsFramer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,
            #    strict=True,
            # TLS setup parameters
            #    sslctx=None,
            #    certfile=None,
            #    keyfile=None,
            #    password=None,
            #    server_hostname="localhost",

        client.start()
        ...
        client.stop()
"""
import logging
import socket
import time

from pymodbus.client.helper_tls import sslctx_provider
from pymodbus.client.sync_tcp import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusTlsFramer

_logger = logging.getLogger(__name__)


class ModbusTlsClient(ModbusTcpClient):
    r"""Modbus client for TLS communication.

    :param host: (positional) Host IP address
    :param port: (optional default 802) The serial port used for communication.
    :param framer: (optional, default ModbusSocketFramer) Framer class.
    :param source_address: (optional, default none) Source address of client,
    :param sslctx: (optional, default none) SSLContext to use for TLS (default None and auto create)
    :param certfile: (optional, default none) Cert file path for TLS server request
    :param keyfile: (optional, default none) Key file path for TLS server request
    :param password: (optional, default none) Password for for decrypting client"s private key file
    :param server_hostname: (optional, default none) Bind certificate to host,
    :param \*\*kwargs: (optional) Extra experimental parameters for transport
    :return: client object
    """

    def __init__(
        self,
        host,
        port=802,
        framer=ModbusTlsFramer,
        sslctx=None,
        certfile=None,
        keyfile=None,
        password=None,
        server_hostname=None,
        **kwargs,
    ):
        """Initialize Modbus TLS Client."""
        self.sslctx = sslctx_provider(sslctx, certfile, keyfile, password)
        self.certfile = certfile
        self.keyfile = keyfile
        self.password = password
        self.server_hostname = server_hostname
        super().__init__(host, port=port, framer=framer, **kwargs)

    def start(self):
        """Connect to the modbus tls server.

        :returns: True if connection succeeded, False otherwise
        """
        if self.socket:
            return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.source_address:
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
        """Read data from the underlying descriptor."""
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
