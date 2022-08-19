"""Modbus client async TLS communication."""
import asyncio
import logging
import ssl

from pymodbus.client.async_tcp import AsyncModbusTcpClient
from pymodbus.transaction import ModbusTlsFramer, FifoTransactionManager
from pymodbus.client.helper_tls import sslctx_provider
from pymodbus.client.base import ModbusClientProtocol
from pymodbus.framer import ModbusFramer
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


class AsyncModbusTlsClient(AsyncModbusTcpClient):
    """**AsyncModbusTlsClient**.

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
        self.certfile = certfile
        self.keyfile = keyfile
        self.password = password
        self.server_hostname = server_hostname

        if not sslctx:
            self.sslctx = ssl.create_default_context()
            # According to MODBUS/TCP Security Protocol Specification, it is
            # TLSv2 at least
            self.sslctx.options |= ssl.OP_NO_TLSv1_1
            self.sslctx.options |= ssl.OP_NO_TLSv1
            self.sslctx.options |= ssl.OP_NO_SSLv3
            self.sslctx.options |= ssl.OP_NO_SSLv2
        else:
            self.sslctx = sslctx
        self.certfile = certfile
        self.keyfile = keyfile
        self.password = password
        self.server_hostname = server_hostname
        AsyncModbusTcpClient.__init__(self, host, port=port, framer=framer, **kwargs)

    async def connect(self):
        """Initiate connection to start client.

        :meta private:
        """
        # get current loop, if there are no loop a RuntimeError will be raised
        self.loop = asyncio.get_running_loop()
        return await AsyncModbusTcpClient.connect(self)

    async def _connect(self):
        """Connect to server."""
        _logger.debug("Connecting.")
        try:
            return await self.loop.create_connection(
                self._create_protocol,
                self.params.host,
                self.params.port,
                ssl=self.sslctx,
                server_hostname=self.server_hostname,
            )
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Failed to connect: {exc}"
            _logger.warning(txt)
            asyncio.ensure_future(self._reconnect())
        else:
            txt = f"Connected to {self.params.host}:{self.params.port}."
            _logger.info(txt)
            self.reset_delay()

    def _create_protocol(self):
        """Create initialized protocol instance with Factory function."""
        protocol = ModbusClientProtocol(framer=self.framer, **self.params.kwargs)
        protocol.transaction = FifoTransactionManager(self)
        protocol.factory = self
        return protocol
