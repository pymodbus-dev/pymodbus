"""Common logic of asynchronous client."""
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.transaction import FifoTransactionManager
from pymodbus.transaction import DictTransactionManager
from pymodbus.client.common import ModbusClientMixin


#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging

_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Connected Client Protocols
#---------------------------------------------------------------------------#
class AsyncModbusClientMixin(ModbusClientMixin):
    """Abstract asynchronous protocol running high level modbus logic on top
    of asynchronous loop.

    Behavior specific to an asynchronous framework like Twisted or asyncio is
    implemented in a derived class.
    """

    transport = None

    def __init__(self, framer=None):
        ''' Initializes the framer module

        :param framer: The framer to use for the protocol.
        '''
        self._connected = False
        self.framer = framer or ModbusSocketFramer(ClientDecoder())

        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self)
        else:
            self.transaction = FifoTransactionManager(self)

    def _connectionMade(self):
        ''' Called upon a successful client connection.
        '''
        _logger.debug("Client connected to modbus server")
        self._connected = True

    def _connectionLost(self, reason):
        ''' Called upon a client disconnect

        :param reason: The reason for the disconnect
        '''
        _logger.debug("Client disconnected from modbus server: %s" % reason)
        self._connected = False
        for tid in list(self.transaction):
            self.raise_future(self.transaction.getTransaction(tid), ConnectionException('Connection lost during request'))

    def _dataReceived(self, data):
        ''' Get response, check for valid message, decode result

        :param data: The data returned from the server
        '''
        self.framer.processIncomingPacket(data, self._handleResponse)

    def execute(self, request):
        ''' Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        self.transport.write(packet)
        return self._buildResponse(request.transaction_id)

    def _handleResponse(self, reply):
        ''' Handle the processed response and link to correct deferred

        :param reply: The reply to process
        '''
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.getTransaction(tid)
            if handler:
                self.resolve_future(handler, reply)
            else:
                _logger.debug("Unrequested message: " + str(reply))

    def _buildResponse(self, tid):
        ''' Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        '''
        f = self.create_future()
        if not self._connected:
            self.raise_future(f, ConnectionException('Client is not connected'))
        else:
            self.transaction.addTransaction(f, tid)
        return f

    def create_future(self):
        raise NotImplementedError()

    def resolve_future(self, f, result):
        raise NotImplementedError()

    def raise_future(self, f, exc):
        raise NotImplementedError()


#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "AsyncModbusClientMixin",
]
#----------------------------------------------------------------------#