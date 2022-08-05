"""Modbus client async TLS communication.

Example::

    from pymodbus.client import AsyncModbusTlsClient

    async def run():
        client = AsyncModbusTlsClient(
            "localhost",
            #    port=802,
            # Common optional paramers:
            #    protocol_class=None,
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

        await client.start()
        ...
        await client.stop()
"""
import asyncio
import logging
import ssl

from pymodbus.factory import ClientDecoder
from pymodbus.client.async_tcp import AsyncModbusTcpClient
from pymodbus.transaction import ModbusTlsFramer, FifoTransactionManager
from pymodbus.client.helper_tls import sslctx_provider

_logger = logging.getLogger(__name__)


class AsyncModbusTlsClient(AsyncModbusTcpClient):  # pylint: disable=too-many-instance-attributes
    r"""Modbus client for async TLS communication.

    :param host: (positional) Host IP address
    :param port: (optional default 502) The serial port used for communication.
    :param protocol_class: (optional, default ModbusClientProtocol) Protocol communication class.
    :param modbus_decoder: (optional, default ClientDecoder) Message decoder class.
    :param framer: (optional, default ModbusSocketFramer) Framer class.
    :param timeout: (optional, default 3s) Timeout for a request.
    :param retries: (optional, default 3) Max number of retries pr request.
    :param retry_on_empty: (optional, default false) Retry on empty response.
    :param close_comm_on_error: (optional, default true) Close connection on error.
    :param strict: (optional, default true) Strict timing, 1.5 character between requests.
    :param source_address: (optional, default none) Source address of client,
    :param sslctx: (optional, default none) SSLContext to use for TLS (default None and auto create)
    :param certfile: (optional, default none) Cert file path for TLS server request
    :param keyfile: (optional, default none) Key file path for TLS server request
    :param password: (optional, default none) Password for for decrypting client"s private key file
    :param server_hostname: (optional, default none) Bind certificate to host,
    :param \*\*kwargs: (optional) Extra experimental parameters for transport
    :return: client object
    """

    def __init__(  # pylint: disable=too-many-arguments
        # Fixed parameters
        self,
        host,
        port=802,
        # Common optional paramers:
        protocol_class=None,
        modbus_decoder=ClientDecoder,
        framer=ModbusTlsFramer,
        timeout=10,
        retries=3,
        retry_on_empty=False,
        close_comm_on_error=False,
        strict=True,

        # TLS setup parameters
        sslctx=None,
        certfile=None,
        keyfile=None,
        password=None,
        server_hostname=None,

        # Extra parameters for transport (experimental)
        **kwargs,
    ):
        r"""Modbus async TLS client.

        :param host: (positional) Host IP address
        :param port: (optional default 802) The serial port used for communication.
        :param protocol_class: (optional, default ModbusClientProtocol) Protocol communication class.
        :param modbus_decoder: (optional, default ClientDecoder) Message decoder class.
        :param framer: (optional, default ModbusSocketFramer) Framer class.
        :param timeout: (optional, default 3s) Timeout for a request.
        :param retries: (optional, default 3) Max number of retries pr request.
        :param retry_on_empty: (optional, default false) Retry on empty response.
        :param close_comm_on_error: (optional, default true) Close connection on error.
        :param strict: (optional, default true) Strict timing, 1.5 character between requests.
        :param source_address: (optional, default none) Source address of client,
        :param sslctx: (optional, default none) SSLContext to use for TLS (default None and auto create)
        :param certfile: (optional, default none) Cert file path for TLS server request
        :param keyfile: (optional, default none) Key file path for TLS server request
        :param password: (optional, default none) Password for for decrypting client"s private key file
        :param server_hostname: (optional, default none) Bind certificate to host,
        :param \*\*kwargs: (optional) Extra experimental parameters for transport
        :return: client object
        """
        self.host = host
        self.port = port
        self.protocol_class = protocol_class
        self.framer = framer(modbus_decoder())
        self.timeout = timeout
        self.retries = retries
        self.retry_on_empty = retry_on_empty
        self.close_comm_on_error = close_comm_on_error
        self.strict = strict
        self.sslctx = sslctx_provider(sslctx, certfile, keyfile, password)
        self.certfile = certfile
        self.keyfile = keyfile
        self.password = password
        self.server_hostname = server_hostname
        self.kwargs = kwargs

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
        AsyncModbusTcpClient.__init__(self, host, port=self.port, framer=framer, **kwargs)

    async def start(self):
        """Initiate connection to start client."""
        # get current loop, if there are no loop a RuntimeError will be raised
        self.loop = asyncio.get_running_loop()
        return await AsyncModbusTcpClient.start(self)

    async def _connect(self):
        _logger.debug("Connecting.")
        try:
            return await self.loop.create_connection(
                self._create_protocol,
                self.host,
                self.port,
                ssl=self.sslctx,
                server_hostname=self.server_hostname,
            )
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Failed to connect: {exc}"
            _logger.warning(txt)
            asyncio.ensure_future(self._reconnect())
        else:
            txt = f"Connected to {self.host}:{self.port}."
            _logger.info(txt)
            self.reset_delay()

    def _create_protocol(self):
        """Create initialized protocol instance with Factory function."""
        protocol = self.protocol_class(framer=self.framer, **self.kwargs)
        protocol.transaction = FifoTransactionManager(self)
        protocol.factory = self
        return protocol
