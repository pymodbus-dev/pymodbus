"""TLS communication."""
import asyncio
import logging
import ssl

from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.transaction import ModbusTlsFramer, FifoTransactionManager

_logger = logging.getLogger(__name__)


class AsyncModbusTLSClient(AsyncModbusTCPClient):
    """Actual Async TLS Client to be used.

    To use do::
        from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
    """

    def __init__(
        self,
        host,
        port=802,
        # TLS setup parameters
        sslctx=None,  # ssl control
        certfile=None,  # certificate file
        keyfile=None,  # key file
        password=None,  # pass phrase
        server_hostname="localhost",  # used for cert verification
        # Extra parameters for tcp
        **kwargs
    ):
        """Initialize AsyncModbusTLSClient.

        :param host: Host IP address
        :param port: The serial port to attach to
        :param protocol_class: Protocol used to talk to modbus device.
        :param modbus_decoder: Message decoder.
        :param framer: Modbus framer
        :param timeout: The timeout between serial requests (default 3s)

        :param source_address: source address specific to underlying backend
        :param sslctx: The SSLContext to use for TLS (default None and auto create)
        :param certfile: The optional client"s cert file path for TLS server request
        :param keyfile: The optional client"s key file path for TLS server request
        :param password: The password for for decrypting client"s private key file
        :param server_hostname: originating host.

        :param kwargs: Other extra args specific to Backend being used
        :return: client object
        """
        self.host = host
        self.port = port
        framer = kwargs.pop("framer", ModbusTlsFramer)

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
        AsyncModbusTCPClient.__init__(self, host, port=self.port, framer=framer, **kwargs)

    async def start(self):
        """Initiate connection to start client."""
        # get current loop, if there are no loop a RuntimeError will be raised
        self.loop = asyncio.get_running_loop()
        return await AsyncModbusTCPClient.start(self)

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
