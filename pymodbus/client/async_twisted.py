"""Asynchronous adapter implementation for Twisted."""
from twisted.internet import defer, protocol
from twisted.python.failure import Failure
from pymodbus.client.async_common import AsyncModbusClientMixin


class ModbusClientProtocol(protocol.Protocol, AsyncModbusClientMixin):
    """Twisted specific implementation of asynchronous modbus client protocol."""

    def connectionMade(self):
        self._connectionMade()

    def connectionLost(self, reason=protocol.connectionDone):
        self._connectionLost(reason)

    def dataReceived(self, data):
        self._dataReceived(data)

    def create_future(self):
        return defer.Deferred()

    def resolve_future(self, f, result):
        f.callback(result)

    def raise_future(self, f, exc):
        f.errback(Failure(exc))
