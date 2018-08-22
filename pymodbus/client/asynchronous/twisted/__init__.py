"""
Implementation of a Modbus Client Using Twisted
--------------------------------------------------

Example run::

    from twisted.internet import reactor, protocol
    from pymodbus.client.asynchronous import ModbusClientProtocol

    def printResult(result):
        print "Result: %d" % result.bits[0]

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
from __future__ import unicode_literals
from twisted.internet import defer, protocol

from pymodbus.exceptions import ConnectionException
from pymodbus.factory import ClientDecoder
from pymodbus.client.asynchronous import AsyncModbusClientMixin
from pymodbus.transaction import FifoTransactionManager, DictTransactionManager
from pymodbus.transaction import ModbusSocketFramer, ModbusRtuFramer
from pymodbus.compat import  byte2int
from twisted.python.failure import Failure


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Connected Client Protocols
# --------------------------------------------------------------------------- #
class ModbusClientProtocol(protocol.Protocol,
                           AsyncModbusClientMixin):
    """
    This represents the base modbus client protocol.  All the application
    layer code is deferred to a higher level wrapper.
    """
    framer = None

    def __init__(self, framer=None, **kwargs):
        self._connected = False
        if framer:
            self.framer = framer

        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self, **kwargs)

        else:
            self.transaction = FifoTransactionManager(self, **kwargs)

    def connectionMade(self):
        """ 
        Called upon a successful client connection.
        """
        _logger.debug("Client connected to modbus server")
        self._connected = True

    def connectionLost(self, reason=None):
        """ 
        Called upon a client disconnect

        :param reason: The reason for the disconnect
        """
        _logger.debug("Client disconnected from modbus server: %s" % reason)
        self._connected = False
        for tid in list(self.transaction):
            self.transaction.getTransaction(tid).errback(Failure(
                ConnectionException('Connection lost during request')))

    def dataReceived(self, data):
        """ 
        Get response, check for valid message, decode result

        :param data: The data returned from the server
        """
        _logger.debug("recv: " + " ".join([hex(byte2int(x)) for x in data]))
        self.framer.processIncomingPacket(data, self._handleResponse)

    def execute(self, request):
        """ 
        Starts the producer to send the next request to
        consumer.write(Frame(request))
        """
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        _logger.debug("send: " + " ".join([hex(byte2int(x)) for x in packet]))
        self.transport.write(packet)
        return self._buildResponse(request.transaction_id)

    def _handleResponse(self, reply, **kwargs):
        """ 
        Handle the processed response and link to correct deferred

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.getTransaction(tid)
            if handler:
                handler.callback(reply)
            else: _logger.debug("Unrequested message: " + str(reply))

    def _buildResponse(self, tid):
        """ 
        Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        if not self._connected:
            return defer.fail(Failure(
                ConnectionException('Client is not connected')))

        d = defer.Deferred()
        self.transaction.addTransaction(d, tid)
        return d

    def close(self):
        """
        Closes underlying transport layer ,essentially closing the client
        :return: 
        """
        if self.transport and hasattr(self.transport, "close"):
            self.transport.close()
        self._connected = False


class ModbusTcpClientProtocol(ModbusClientProtocol):
    """
    Async TCP Client protocol based on twisted.
    
    Default framer: ModbusSocketFramer
    """
    framer = ModbusSocketFramer(ClientDecoder())


class ModbusSerClientProtocol(ModbusClientProtocol):
    """
    Async Serial Client protocol based on twisted
    
    Default framer: ModbusRtuFramer
    """
    framer = ModbusRtuFramer(ClientDecoder())


# --------------------------------------------------------------------------- #
# Not Connected Client Protocol
# --------------------------------------------------------------------------- #
class ModbusUdpClientProtocol(protocol.DatagramProtocol, 
                              AsyncModbusClientMixin):
    """
    This represents the base modbus client protocol.  All the application
    layer code is deferred to a higher level wrapper.
    """

    def datagramReceived(self, data, params):
        """
        Get response, check for valid message, decode result

        :param data: The data returned from the server
        :param params: The host parameters sending the datagram
        """
        _logger.debug("Datagram from: %s:%d" % params)
        self.framer.processIncomingPacket(data, self._handleResponse)

    def execute(self, request):
        """
        Starts the producer to send the next request to
        consumer.write(Frame(request))
        """
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        self.transport.write(packet, (self.host, self.port))
        return self._buildResponse(request.transaction_id)

    def _handleResponse(self, reply, **kwargs):
        """
        Handle the processed response and link to correct deferred

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.getTransaction(tid)
            if handler:
                handler.callback(reply)
            else: _logger.debug("Unrequested message: " + str(reply))

    def _buildResponse(self, tid):
        """
        Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        d = defer.Deferred()
        self.transaction.addTransaction(d, tid)
        return d


# --------------------------------------------------------------------------- #
# Client Factories
# --------------------------------------------------------------------------- #
class ModbusClientFactory(protocol.ReconnectingClientFactory):
    """ Simple client protocol factory """

    protocol = ModbusClientProtocol

# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = [
    "ModbusClientProtocol",
    "ModbusUdpClientProtocol",
    "ModbusClientFactory"
]

