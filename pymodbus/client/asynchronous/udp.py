"""UDP communication."""
import asyncio
import logging
import functools

from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.client.async_helper import BaseModbusAsyncClientProtocol

_logger = logging.getLogger(__name__)


class ModbusUdpClientProtocol(BaseModbusAsyncClientProtocol, asyncio.DatagramProtocol):
    """Asyncio specific implementation of asynchronous modbus udp client protocol."""

    #: Factory that created this instance.
    factory = None

    def __init__(self, host=None, port=0, framer=None, **kwargs):
        """Initialize."""
        self.host = host
        self.port = port
        self.framer = framer if framer else ModbusSocketFramer
        super().__init__(**kwargs)

    def datagram_received(self, data, addr):
        """Receive datagram."""
        self._data_received(data)

    def write_transport(self, packet):
        """Write transport."""
        return self.transport.sendto(packet)


class AsyncModbusUDPClient:
    """Actual Async UDP Client to be used.

    To use do::
        from pymodbus.client.asynchronous.tcp import AsyncModbusUDPClient
    """

    #: Reconnect delay in milli seconds.
    delay_ms = 0
    #: Maximum delay in milli seconds before reconnect is attempted.
    DELAY_MAX_MS = 1000 * 60 * 5

    def __init__(
        self,
        host,
        port=502,
        protocol_class=ModbusUdpClientProtocol,
        modbus_decoder=ClientDecoder,
        framer=ModbusSocketFramer,
        timeout=10,
        # TCP setup parameters
        source_address="127.0.0.1",
        # Extra parameters for serial_async (experimental)
        **kwargs,

    ):
        """Initialize AsyncioModbusUDPClient.

        :param host: Host IP address
        :param port: The serial port to attach to
        :param protocol_class: Protocol used to talk to modbus device.
        :param modbus_decoder: Message decoder.
        :param framer: Modbus framer
        :param timeout: The timeout between serial requests (default 3s)

        :param source_address: source address specific to underlying backend

        :param kwargs: Other extra args specific to Backend being used
        :return: client object
        """
        self.host = host
        self.port = port
        self.protocol_class = protocol_class
        self.framer = framer(modbus_decoder())
        self.timeout = timeout

        self.source_address = source_address

        self.loop = None
        self.protocol = None
        self.connected = False
        self.kwargs = kwargs
        self.reset_delay()

    def reset_delay(self):
        """Reset wait before next reconnect to minimal period."""
        self.delay_ms = 100

    async def start(self):
        """Start reconnecting asynchronous udp client."""
        # force reconnect if required:
        self.stop()
        # get current loop, if there are no loop a RuntimeError will be raised
        self.loop = asyncio.get_running_loop()

        txt = f"Connecting to {self.host}:{self.port}."
        _logger.debug(txt)

        # getaddrinfo returns a list of tuples
        # - [(family, type, proto, canonname, sockaddr),]
        # We want sockaddr which is a (ip, port) tuple
        # udp needs ip addresses, not hostnames
        # addrinfo = await self.loop.getaddrinfo(self.host, self.port, type=DGRAM_TYPE)
        # self.host, self.port = addrinfo[0][-1]
        return await self._connect()

    def stop(self):
        """Stop connection and prevents reconnect."""
        # prevent reconnect:
        self.host = None

        if self.connected and self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def _create_protocol(self, host=None, port=0):
        """Create initialized protocol instance with factory function."""
        protocol = self.protocol_class(**self.kwargs)
        protocol.host = host
        protocol.port = port
        protocol.factory = self
        return protocol

    async def _connect(self):
        """Connect."""
        _logger.debug("Connecting.")
        try:
            endpoint = await self.loop.create_datagram_endpoint(
                functools.partial(
                    self._create_protocol, host=self.host, port=self.port
                ),
                remote_addr=(self.host, self.port),
            )
            txt = f"Connected to {self.host}:{self.port}."
            _logger.info(txt)
            return endpoint
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Failed to connect: {exc}"
            _logger.warning(txt)
            asyncio.ensure_future(self._reconnect())

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
            if self.host:
                asyncio.create_task(self._reconnect())
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    async def _reconnect(self):
        """Reconnect."""
        txt = f"Waiting {self.delay_ms} ms before next connection attempt."
        _logger.debug(txt)
        await asyncio.sleep(self.delay_ms / 1000)
        self.delay_ms = min(2 * self.delay_ms, self.DELAY_MAX_MS)
        return await self._connect()
