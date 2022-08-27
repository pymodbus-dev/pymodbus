"""Modbus client TLS communication."""
import logging
import socket

from pymodbus.client.async_tls import sslctx_provider
from pymodbus.client.sync_tcp import ModbusTcpClient
from pymodbus.constants import Defaults
from pymodbus.framer import ModbusFramer
from pymodbus.framer.tls_framer import ModbusTlsFramer


_logger = logging.getLogger(__name__)


class ModbusTlsClient(ModbusTcpClient):
    """**ModbusTlsClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication.
    :param framer: (optional) Framer class.
    :param source_address: (optional) Source address of client,
    :param sslctx: (optional) SSLContext to use for TLS
    :param certfile: (optional) Cert file path for TLS server request
    :param keyfile: (optional) Key file path for TLS server request
    :param password: (optional) Password for for decrypting private key file
    :param server_hostname: (optional) Bind certificate to host,
    :param kwargs: (optional) Experimental parameters.

    Example::

        from pymodbus.client import ModbusTlsClient

        async def run():
            client = ModbusTlsClient("localhost")

            client.connect()
            ...
            client.close()
    """

    def __init__(
        self,
        host: str,
        port: int = Defaults.TlsPort,
        framer: ModbusFramer = ModbusTlsFramer,
        sslctx: str = None,
        certfile: str = None,
        keyfile: str = None,
        password: str = None,
        server_hostname: str = None,
        **kwargs: any,
    ):
        """Initialize Modbus TLS Client."""
        super().__init__(host, port=port, framer=framer, **kwargs)
        self.sslctx = sslctx_provider(sslctx, certfile, keyfile, password)
        self.certfile = certfile
        self.keyfile = keyfile
        self.password = password
        self.server_hostname = server_hostname

    @property
    def connected(self):
        """Connect internal."""
        return self.connect()

    def connect(self):
        """Connect to the modbus tls server."""
        if self.socket:
            return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.source_address:
                sock.bind(self.source_address)
            self.socket = self.sslctx.wrap_socket(
                sock, server_side=False, server_hostname=self.params.host
            )
            self.socket.settimeout(self.params.timeout)
            self.socket.connect((self.params.host, self.params.port))
        except socket.error as msg:
            txt = (
                f"Connection to ({self.params.host}, {self.params.port}) failed: {msg}"
            )
            _logger.error(txt)
            self.close()
        return self.socket is not None

    def __str__(self):
        """Build a string representation of the connection."""
        return f"ModbusTlsClient({self.params.host}:{self.params.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.params.host}, port={self.params.port}, sslctx={self.sslctx}, "
            f"timeout={self.params.timeout}>"
        )
