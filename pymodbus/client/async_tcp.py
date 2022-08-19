"""Modbus client async TCP communication."""
import asyncio
import logging
import typing

from pymodbus.framer import ModbusFramer
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.client.base import ModbusBaseClient
from pymodbus.client.base import ModbusClientProtocol
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


class AsyncModbusTcpClient(ModbusBaseClient):
    """**AsyncModbusTcpClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication.
    :param framer: (optional) Framer class.
    :param source_address: (optional) source address of client,
    :param kwargs: (optional) Experimental parameters

    Example::

        from pymodbus.client import AsyncModbusTcpClient

        async def run():
            client = AsyncModbusTcpClient("localhost")

            await client.connect()
            ...
            await client.close()
    """

    def __init__(
        self,
        host: str,
        port: int = Defaults.TcpPort,
        framer: ModbusFramer = ModbusSocketFramer,
        source_address: typing.Tuple[str, int] = None,
        **kwargs: any,
    ) -> None:
        """Initialize Asyncio Modbus TCP Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.host = host
        self.params.port = port
        self.source_address = source_address
        self.loop = None
        self.protocol = None
        self.connected = False
        self.delay_ms = self.params.reconnect_delay

    async def connect(self):  # pylint: disable=invalid-overridden-method
        """Initiate connection to start client.

        :meta private:
        """
        # force reconnect if required:
        self.loop = asyncio.get_running_loop()

        txt = f"Connecting to {self.params.host}:{self.params.port}."
        _logger.debug(txt)
        return await self._connect()

    async def close(self):  # pylint: disable=invalid-overridden-method
        """Stop client.

        :meta private:
        """
        if self.connected and self.protocol and self.protocol.transport:
            self.protocol.transport.close()

        # prevent reconnect.
        self.params.host = None

    def _create_protocol(self):
        """Create initialized protocol instance with factory function."""
        protocol = ModbusClientProtocol(framer=self.params.framer, **self.params.kwargs)
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
        """Notify successful connection.

        :meta private:
        """
        _logger.info("Protocol made connection.")
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    def protocol_lost_connection(self, protocol):
        """Notify lost connection.

        :meta private:
        """
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
        self.delay_ms = 2 * self.delay_ms

        return await self._connect()
