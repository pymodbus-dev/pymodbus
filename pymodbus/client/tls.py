"""Modbus client async TLS communication."""
import asyncio
import socket
import ssl

from pymodbus.client.tcp import AsyncModbusTcpClient, ModbusTcpClient
from pymodbus.constants import Defaults
from pymodbus.framer import ModbusFramer
from pymodbus.framer.tls_framer import ModbusTlsFramer
from pymodbus.logging import Log


def sslctx_provider(
    sslctx=None, certfile=None, keyfile=None, password=None
):  # pylint: disable=missing-type-doc
    """Provide the SSLContext for ModbusTlsClient.

    If the user defined SSLContext is not passed in, sslctx_provider will
    produce a default one.

    :param sslctx: The user defined SSLContext to use for TLS (default None and
                   auto create)
    :param certfile: The optional client's cert file path for TLS server request
    :param keyfile: The optional client's key file path for TLS server request
    :param password: The password for decrypting client's private key file
    """
    if sslctx:
        return sslctx

    sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    sslctx.check_hostname = False
    sslctx.verify_mode = ssl.CERT_NONE
    sslctx.options |= ssl.OP_NO_TLSv1_1
    sslctx.options |= ssl.OP_NO_TLSv1
    sslctx.options |= ssl.OP_NO_SSLv3
    sslctx.options |= ssl.OP_NO_SSLv2
    if certfile and keyfile:
        sslctx.load_cert_chain(certfile=certfile, keyfile=keyfile, password=password)
    return sslctx


class AsyncModbusTlsClient(AsyncModbusTcpClient):
    """**AsyncModbusTlsClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication
    :param framer: (optional) Framer class
    :param source_address: (optional) Source address of client
    :param sslctx: (optional) SSLContext to use for TLS
    :param certfile: (optional) Cert file path for TLS server request
    :param keyfile: (optional) Key file path for TLS server request
    :param password: (optional) Password for for decrypting private key file
    :param server_hostname: (optional) Bind certificate to host
    :param kwargs: (optional) Experimental parameters

    Example::

        from pymodbus.client import AsyncModbusTlsClient

        async def run():
            client = AsyncModbusTlsClient("localhost")

            await client.connect()
            ...
            await client.close()
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
        """Initialize Asyncio Modbus TLS Client."""
        super().__init__(host, port=port, framer=framer, **kwargs)
        self.sslctx = sslctx_provider(sslctx, certfile, keyfile, password)
        self.params.sslctx = sslctx
        self.params.certfile = certfile
        self.params.keyfile = keyfile
        self.params.password = password
        self.params.server_hostname = server_hostname
        AsyncModbusTcpClient.__init__(self, host, port=port, framer=framer, **kwargs)

    async def _connect(self):
        """Connect to server."""
        Log.debug("Connecting tls.")
        try:
            return await self.loop.create_connection(
                self._create_protocol,
                self.params.host,
                self.params.port,
                ssl=self.sslctx,
                server_hostname=self.params.server_hostname,
            )
        except Exception as exc:  # pylint: disable=broad-except
            Log.warning("Failed to connect: {}", exc)
            if self.delay_ms > 0:
                asyncio.ensure_future(self._reconnect())
            return
        Log.info("Connected to {}:{}.", self.params.host, self.params.port)
        self.reset_delay()


class ModbusTlsClient(ModbusTcpClient):
    """**ModbusTlsClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication
    :param framer: (optional) Framer class
    :param source_address: (optional) Source address of client
    :param sslctx: (optional) SSLContext to use for TLS
    :param certfile: (optional) Cert file path for TLS server request
    :param keyfile: (optional) Key file path for TLS server request
    :param password: (optional) Password for decrypting private key file
    :param server_hostname: (optional) Bind certificate to host
    :param kwargs: (optional) Experimental parameters

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
        self.params.sslctx = sslctx
        self.params.certfile = certfile
        self.params.keyfile = keyfile
        self.params.password = password
        self.params.server_hostname = server_hostname

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
            if self.params.source_address:
                sock.bind(self.params.source_address)
            self.socket = self.sslctx.wrap_socket(
                sock, server_side=False, server_hostname=self.params.host
            )
            self.socket.settimeout(self.params.timeout)
            self.socket.connect((self.params.host, self.params.port))
        except socket.error as msg:
            Log.error(
                "Connection to ({}, {}) failed: {}",
                self.params.host,
                self.params.port,
                msg,
            )
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
