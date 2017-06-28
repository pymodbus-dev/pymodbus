"""Asynchronous framework adapter for asyncio."""
import asyncio
from pymodbus.client.async_common import AsyncModbusClientMixin
import logging

_logger = logging.getLogger(__name__)


class ModbusClientProtocol(asyncio.Protocol, AsyncModbusClientMixin):
    """Asyncio specific implementation of asynchronous modubus client protocol."""

    #: Factory that created this instance.
    factory = None

    def connection_made(self, transport):
        self.transport = transport
        self._connectionMade()

        if self.factory:
            self.factory.protocol_made_connection(self)

    def connection_lost(self, reason):
        self.transport = None
        self._connectionLost(reason)

        if self.factory:
            self.factory.protocol_lost_connection(self)

    def data_received(self, data):
        self._dataReceived(data)

    def create_future(self):
        return asyncio.Future()

    def resolve_future(self, f, result):
        f.set_result(result)

    def raise_future(self, f, exc):
        f.set_exception(exc)


class ReconnectingAsyncioModbusTcpClient(object):
    """Client to connect to modbus device repeatedly over TCP/IP."""

    #: Reconnect delay in milli seconds.
    delay_ms = 0

    #: Maximum delay in milli seconds before reconnect is attempted.
    DELAY_MAX_MS = 1000 * 60 * 5

    def __init__(self, protocol_class=None, loop=None):
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusClientProtocol
        #: Current protocol instance.
        self.protocol = None
        #: Event loop to use.
        self.loop = loop or asyncio.get_event_loop()

        self.host = None
        self.port = 0

        self.connected = False
        self.reset_delay()

    def reset_delay(self):
        """Resets wait before next reconnect to minimal period."""
        self.delay_ms = 100

    @asyncio.coroutine
    def start(self, host, port=502):
        # force reconnect if required:
        self.stop()

        _logger.debug('Connecting to %s:%s.' % (host, port))
        self.host = host
        self.port = port

        yield from self._connect()

    def stop(self):
        # prevent reconnect:
        self.host = None

        if self.connected:
            if self.protocol:
                if self.protocol.transport:
                    self.protocol.transport.close()

    def _create_protocol(self):
        """Factory function to create initialized protocol instance."""
        protocol = self.protocol_class()
        protocol.factory = self
        return protocol

    @asyncio.coroutine
    def _connect(self):
        _logger.debug('Connecting.')
        try:
            yield from self.loop.create_connection(self._create_protocol, self.host, self.port)
            _logger.info('Connected to %s:%s.' % (self.host, self.port))
        except Exception as ex:
            _logger.warning('Failed to connect: %s' % ex)
            asyncio.async(self._reconnect(), loop=self.loop)

    def protocol_made_connection(self, protocol):
        """Protocol notification of successful connection."""
        _logger.info('Protocol made connection.')
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error('Factory protocol connect callback called while connected.')

    def protocol_lost_connection(self, protocol):
        """Protocol notification of lost connection."""
        if self.connected:
            _logger.info('Protocol lost connection.')
            if protocol is not self.protocol:
                _logger.error('Factory protocol callback called from unexpected protocol instance.')

            self.connected = False
            self.protocol = None
            if self.host:
                asyncio.async(self._reconnect(), loop=self.loop)
        else:
            _logger.error('Factory protocol disconnect callback called while not connected.')

    @asyncio.coroutine
    def _reconnect(self):
        _logger.debug('Waiting %d ms before next connection attempt.' % self.delay_ms)
        yield from asyncio.sleep(self.delay_ms / 1000)
        self.delay_ms = min(2 * self.delay_ms, self.DELAY_MAX_MS)
        yield from self._connect()
