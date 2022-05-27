"""Implementation of a Modbus Client Using Twisted

Example run::

    from twisted.internet import reactor, protocol
    from pymodbus.client.asynchronous import ModbusClientProtocol

    def printResult(result):
        print("Result: %d" % result.bits[0])

    def process(client):
        result = client.write_coil(1, True)
        result.addCallback(printResult)
        reactor.callLater(1, reactor.stop)

    defer = protocol.ClientCreator(reactor, ModbusClientProtocol
            ).connectTCP("localhost", 502)
    defer.addCallback(process)

Another example::

    from twisted.internet import reactor
    from pymodbus.client.asynchronous import ModbusClientFactory

    def process():
        factory = reactor.connectTCP("localhost", 502, ModbusClientFactory())
        reactor.stop()

    if __name__ == "__main__":
       reactor.callLater(1, process)
       reactor.run()
"""
import logging

from twisted.internet import defer, protocol
from twisted.python.failure import Failure

from pymodbus.exceptions import ConnectionException
from pymodbus.factory import ClientDecoder
from pymodbus.client.asynchronous.mixins import AsyncModbusClientMixin
from pymodbus.transaction import FifoTransactionManager, DictTransactionManager
from pymodbus.transaction import ModbusSocketFramer, ModbusRtuFramer
from pymodbus.utilities import hexlify_packets


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Connected Client Protocols
# --------------------------------------------------------------------------- #
class ModbusClientProtocol(protocol.Protocol, AsyncModbusClientMixin):
    """This represents the base modbus client protocol.

    All the application layer code is deferred to a higher level wrapper.
    """

    framer = None

    def __init__(self, framer=None, **kwargs):  # pylint: disable=super-init-not-called
        """Initialize."""
        self._connected = False
        self.framer = framer or ModbusSocketFramer(ClientDecoder())
        if isinstance(self.framer, type):
            # Framer class not instance
            self.framer = self.framer(ClientDecoder(), client=None)
        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self, **kwargs)
        else:
            self.transaction = FifoTransactionManager(self, **kwargs)

    def connectionMade(self):
        """Call upon a successful client connection."""
        _logger.debug("Client connected to modbus server")
        self._connected = True

    def connectionLost(self, reason=None):
        """Call upon a client disconnect.

        :param reason: The reason for the disconnect
        """
        txt = f"Client disconnected from modbus server: {reason}"
        _logger.debug(txt)
        self._connected = False
        for tid in list(self.transaction):
            self.transaction.getTransaction(tid).errback(
                Failure(ConnectionException("Connection lost during request"))
            )

    def dataReceived(self, data):
        """Get response, check for valid message, decode result.

        :param data: The data returned from the server
        """
        unit = self.framer.decode_data(data).get("unit", 0)
        self.framer.processIncomingPacket(data, self._handleResponse, unit=unit)

    def execute(self, request=None):
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        txt = f"send: {hexlify_packets(packet)}"
        _logger.debug(txt)
        self.transport.write(packet)
        return self._buildResponse(request.transaction_id)

    def _handleResponse(
        self, reply, **kwargs
    ):  # pylint: disable=invalid-name,unused-argument
        """Handle the processed response and link to correct deferred.

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                handler.callback(reply)
            else:
                txt = f"Unrequested message: {str(reply)}"
                _logger.debug(txt)

    def _buildResponse(self, tid):  # pylint: disable=invalid-name,
        """Return a deferred response for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        if not self._connected:
            return defer.fail(Failure(ConnectionException("Client is not connected")))

        deferred = defer.Deferred()
        self.transaction.addTransaction(deferred, tid)
        return deferred

    def close(self):
        """Close underlying transport layer ,essentially closing the client.

        :return:
        """
        if self.transport and hasattr(self.transport, "close"):
            self.transport.close()
        self._connected = False


class ModbusTcpClientProtocol(ModbusClientProtocol):
    """Async TCP Client protocol based on twisted.

    Default framer: ModbusSocketFramer
    """

    framer = ModbusSocketFramer(ClientDecoder())


class ModbusSerClientProtocol(ModbusClientProtocol):
    """Async Serial Client protocol based on twisted.

    Default framer: ModbusRtuFramer
    """

    def __init__(self, framer=None, **kwargs):
        framer = framer or ModbusRtuFramer(ClientDecoder())
        super().__init__(framer, **kwargs)


# --------------------------------------------------------------------------- #
# Not Connected Client Protocol
# --------------------------------------------------------------------------- #
class ModbusUdpClientProtocol(protocol.DatagramProtocol, AsyncModbusClientMixin):
    """This represents the base modbus client protocol.

    All the application layer code is deferred to a higher level wrapper.
    """

    def datagramReceived(self, datagram, addr):
        """Get response, check for valid message, decode result.

        :param data: The data returned from the server
        :param params: The host parameters sending the datagram
        """
        txt = f"Datagram from: {addr}"
        _logger.debug(txt)
        unit = self.framer.decode_data(datagram).get("uid", 0)
        self.framer.processIncomingPacket(datagram, self._handleResponse, unit=unit)

    def execute(self, request=None):
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        self.transport.write(packet, (self.host, self.port))
        return self._buildResponse(request.transaction_id)

    def _handleResponse(
        self, reply, **kwargs
    ):  # pylint: disable=invalid-name,unused-argument
        """Handle the processed response and link to correct deferred.

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                handler.callback(reply)
            else:
                txt = f"Unrequested message: {str(reply)}"
                _logger.debug(txt)

    def _buildResponse(self, tid):  # pylint: disable=invalid-name
        """Return a deferred response for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        deferred = defer.Deferred()
        self.transaction.addTransaction(deferred, tid)
        return deferred


# --------------------------------------------------------------------------- #
# Client Factories
# --------------------------------------------------------------------------- #
class ModbusClientFactory(protocol.ReconnectingClientFactory):
    """Simple client protocol factory."""

    protocol = ModbusClientProtocol


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = ["ModbusClientProtocol", "ModbusUdpClientProtocol", "ModbusClientFactory"]
