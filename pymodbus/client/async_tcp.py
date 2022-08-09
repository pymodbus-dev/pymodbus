"""**Modbus client async TCP communication.**

Example::

    from pymodbus.client import AsyncModbusTcpClient

    async def run():
        client = AsyncModbusTcpClient(
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
            # TCP setup parameters
            #    source_address=("localhost", 0),
        )

        await client.aStart()
        ...
        await client.aStop()
"""
import asyncio
import logging

from pymodbus.transaction import ModbusSocketFramer
from pymodbus.client.base import ModbusBaseClient
from pymodbus.client.helper_async import ModbusClientProtocol

_logger = logging.getLogger(__name__)


class AsyncModbusTcpClient(ModbusBaseClient):
    r"""Modbus client for async TCP communication.

    :param host: (positional) Host IP address
    :param port: (optional default 502) The TCP port used for communication.
    :param source_address: (optional, default none) source address of client,
    :param \*\*kwargs: (optional) Extra experimental parameters for transport
    :return: client object
    """

    #: Minimum delay in milli seconds before reconnect is attempted.
    DELAY_MIN_MS = 100
    #: Maximum delay in milli seconds before reconnect is attempted.
    DELAY_MAX_MS = 1000 * 60 * 5

    def __init__(
        self,
        host,
        port=502,
        framer=ModbusSocketFramer,
        source_address=None,
        **kwargs,
    ):
        """Initialize Asyncio Modbus TCP Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.host = host
        self.params.port = port
        self.source_address = source_address
        self.loop = None
        self.protocol = None
        self.connected = False
        self.delay_ms = self.DELAY_MIN_MS

    def reset_delay(self):
        """Reset wait before next reconnect to minimal period."""
        self.delay_ms = self.DELAY_MIN_MS

    async def aStart(self):
        """Initiate connection to start client."""
        # force reconnect if required:
        await self.aStop()
        self.loop = asyncio.get_running_loop()

        txt = f"Connecting to {self.params.host}:{self.params.port}."
        _logger.debug(txt)
        return await self._connect()

    async def aStop(self):  # pylint: disable=invalid-name
        """Stop client."""
        # prevent reconnect:
        self.params.host = None

        if self.connected and self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def _create_protocol(self):
        """Create initialized protocol instance with factory function."""
        protocol = ModbusClientProtocol(**self.params.kwargs)
        protocol.factory = self
        return protocol

    async def _connect(self):
        """Connect."""
        _logger.debug("Connecting.")
        try:
            transport, protocol = await self.loop.create_connection(
                self._create_protocol, self.params.host, self.params.port
            )
            return transport, protocol
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Failed to connect: {exc}"
            _logger.warning(txt)
            asyncio.ensure_future(self._reconnect())
        else:
            txt = f"Connected to {self.params.host}:{self.params.port}."
            _logger.info(txt)
            self.reset_delay()

    def protocol_made_connection(self, protocol):
        """Notify successful connection."""
        _logger.info("Protocol made connection.")
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    def protocol_lost_connection(self, protocol):
        """Notify lost connection."""
        if self.connected:
            _logger.info("Protocol lost connection.")
            if protocol is not self.protocol:
                _logger.error(
                    "Factory protocol callback called "
                    "from unexpected protocol instance."
                )

            self.connected = False
            self.protocol = None
            if self.params.host:
                asyncio.ensure_future(self._reconnect())
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    async def _reconnect(self):
        """Reconnect."""
        txt = f"Waiting {self.delay_ms} ms before next connection attempt."
        _logger.debug(txt)
        await asyncio.sleep(self.delay_ms / 1000)
        self.delay_ms = min(2 * self.delay_ms, self.DELAY_MAX_MS)

        return await self._connect()
