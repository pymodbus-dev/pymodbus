"""Implementation of a Modbus Client Using Twisted.

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

from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.transaction import FifoTransactionManager
from pymodbus.transaction import DictTransactionManager
from pymodbus.client.common import ModbusClientMixin
from pymodbus.client.asynchronous.deprecated import deprecated


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Connected Client Protocols
# --------------------------------------------------------------------------- #
class ModbusClientProtocol(protocol.Protocol, ModbusClientMixin):  # pragma: no cover
    """This represents the base modbus client protocol.

    All the application layer code is deferred to a higher level wrapper.
    """

    def __init__(self, framer=None, **kwargs):
        """Initialize the framer module.

        :param framer: The framer to use for the protocol
        """
        deprecated(self.__class__.__name__)
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

    def connectionLost(self, reason):  # pylint: disable=signature-differs
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
        unit = self.framer.decode_data(data).get("uid", 0)
        self.framer.processIncomingPacket(data, self._handle_response, unit=unit)

    def execute(self, request):
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        request.transaction_id = self.transaction.getNextTID()
        self.transport.write(self.framer.buildPacket(request))
        return self._build_response(request.transaction_id)

    def _handle_response(self, reply):
        """Handle the processed response and link to correct deferred.

        :param reply: The reply to process
        """
        if reply is not None:
            if handler := self.transaction.getTransaction(reply.transaction_id):
                handler.callback(reply)
            else:
                txt = f"Unrequested message: {str(reply)}"
                _logger.debug(txt)

    def _build_response(self, tid):
        """Return a deferred response for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        if not self._connected:
            return defer.fail(Failure(ConnectionException("Client is not connected")))

        deferred = defer.Deferred()
        self.transaction.addTransaction(deferred, tid)
        return deferred

    # ---------------------------------------------------------------------- #
    # Extra Functions
    # ---------------------------------------------------------------------- #
    # if send_failed:
    #       if self.retry > 0:
    #               deferLater(clock, self.delay, send, message)
    #               self.retry -= 1


# --------------------------------------------------------------------------- #
# Not Connected Client Protocol
# --------------------------------------------------------------------------- #
class ModbusUdpClientProtocol(
    protocol.DatagramProtocol, ModbusClientMixin
):  # pragma: no cover
    """This represents the base modbus client protocol.

    All the application layer code is deferred to a higher level wrapper.
    """

    def __init__(self, framer=None, **kwargs):
        """Initialize the framer module.

        :param framer: The framer to use for the protocol
        """
        deprecated(self.__class__.__name__)
        self.framer = framer or ModbusSocketFramer(ClientDecoder())
        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self, **kwargs)
        else:
            self.transaction = FifoTransactionManager(self, **kwargs)

    def datagramReceived(self, datagram, addr):
        """Get response, check for valid message, decode result.

        :param data: The data returned from the server
        :param params: The host parameters sending the datagram
        """
        txt = f"Datagram from: {addr}"
        _logger.debug(txt)
        unit = self.framer.decode_data(datagram).get("uid", 0)
        self.framer.processIncomingPacket(datagram, self._handle_response, unit=unit)

    def execute(self, request):
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        self.transport.write(packet)
        return self._build_response(request.transaction_id)

    def _handle_response(self, reply):
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

    def _build_response(self, tid):
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
class ModbusClientFactory(protocol.ReconnectingClientFactory):  # pragma: no cover
    """Simple client protocol factory."""

    protocol = ModbusClientProtocol

    def __init__(self):
        """Initialize."""
        deprecated(self.__class__.__name__)
        protocol.ReconnectingClientFactory.__init__(self)


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = ["ModbusClientProtocol", "ModbusUdpClientProtocol", "ModbusClientFactory"]
