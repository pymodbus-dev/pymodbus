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

from pymodbus.client.helper_tls import sslctx_provider
from pymodbus.client.sync_tcp import ModbusTcpClient
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
        super().__init__(host, port=port, framer=framer, **kwargs)
        self.sslctx = sslctx_provider(sslctx, certfile, keyfile, password)
        self.certfile = certfile
        self.keyfile = keyfile
        self.password = password
        self.server_hostname = server_hostname

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
                sock, server_side=False, server_hostname=self.params.host
            )
            self.socket.settimeout(self.params.timeout)
            self.socket.connect((self.params.host, self.params.port))
        except socket.error as msg:
            txt = f"Connection to ({self.params.host}, {self.params.port}) failed: {msg}"
            _logger.error(txt)
            self.close()
        return self.socket is not None

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"ModbusTlsClient({self.params.host}:{self.params.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.params.host}, port={self.params.port}, sslctx={self.sslctx}, "
            f"timeout={self.params.timeout}>"
        )
