'''
Collection of transaction based abstractions
'''
import struct
import socket
from threading import RLock

from pymodbus.exceptions import ModbusIOException, NotImplementedException
from pymodbus.exceptions import InvalidMessageReceivedException
from pymodbus.constants import Defaults
from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.framer.binary_framer import ModbusBinaryFramer
from pymodbus.utilities import hexlify_packets, ModbusTransactionState
from pymodbus.compat import iterkeys, byte2int


# Python 2 compatibility.
try:
    TimeoutError
except NameError:
    TimeoutError = socket.timeout

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# The Global Transaction Manager
# --------------------------------------------------------------------------- #
class ModbusTransactionManager(object):
    ''' Impelements a transaction for a manager

    The transaction protocol can be represented by the following pseudo code::

        count = 0
        do
          result = send(message)
          if (timeout or result == bad)
             count++
          else break
        while (count < 3)

    This module helps to abstract this away from the framer and protocol.
    '''

    def __init__(self, client, **kwargs):
        ''' Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        :param retry_on_empty: Should the client retry on empty
        :param retries: The number of retries to allow
        '''
        self.tid = Defaults.TransactionId
        self.client = client
        self.retry_on_empty = kwargs.get('retry_on_empty', Defaults.RetryOnEmpty)
        self.retries = kwargs.get('retries', Defaults.Retries) or 1
        self._transaction_lock = RLock()
        self._no_response_devices = []
        if client:
            self._set_adu_size()

    def _set_adu_size(self):
        # base ADU size of modbus frame in bytes
        if isinstance(self.client.framer, ModbusSocketFramer):
            self.base_adu_size = 7  # tid(2), pid(2), length(2), uid(1)
        elif isinstance(self.client.framer, ModbusRtuFramer):
            self.base_adu_size = 3  # address(1), CRC(2)
        elif isinstance(self.client.framer, ModbusAsciiFramer):
            self.base_adu_size = 7  # start(1)+ Address(2), LRC(2) + end(2)
        elif isinstance(self.client.framer, ModbusBinaryFramer):
            self.base_adu_size = 5  # start(1) + Address(1), CRC(2) + end(1)

    def _calculate_response_length(self, expected_pdu_size):
        return self.base_adu_size + expected_pdu_size

    def _calculate_exception_length(self):
        ''' Returns the length of the Modbus Exception Response according to
        the type of Framer.
        '''
        if isinstance(self.client.framer, ModbusSocketFramer):
            return self.base_adu_size + 2  # Fcode(1), ExcecptionCode(1)
        elif isinstance(self.client.framer, ModbusAsciiFramer):
            return self.base_adu_size + 4  # Fcode(2), ExcecptionCode(2)
        elif isinstance(self.client.framer, (ModbusRtuFramer, ModbusBinaryFramer)):
            return self.base_adu_size + 2  # Fcode(1), ExcecptionCode(1)

    def _check_response(self, response):
        ''' Checks if the response is a Modbus Exception.
        '''
        if isinstance(self.client.framer, ModbusSocketFramer):
            if len(response) >= 8 and byte2int(response[7]) > 128:
                return False
        elif isinstance(self.client.framer, ModbusAsciiFramer):
            if len(response) >= 5 and int(response[3:5], 16) > 128:
                return False
        elif isinstance(self.client.framer, (ModbusRtuFramer, ModbusBinaryFramer)):
            if len(response) >= 2 and byte2int(response[1]) > 128:
                return False

        return True

    def execute(self, request):
        ''' Starts the producer to send the next request to
        consumer.write(Frame(request))
        '''
        with self._transaction_lock:
            try:
                _logger.debug("Current transaction state - {}".format(
                    ModbusTransactionState.to_string(self.client.state))
                )
                retries = self.retries
                request.transaction_id = self.getNextTID()
                _logger.debug("Running transaction %d" % request.transaction_id)
                _buffer = hexlify_packets(self.client.framer._buffer)
                if _buffer:
                    _logger.debug("Clearing current Frame : - {}".format(_buffer))
                    self.client.framer.resetFrame()

                expected_response_length = None
                if not isinstance(self.client.framer, ModbusSocketFramer):
                    if hasattr(request, "get_response_pdu_size"):
                        response_pdu_size = request.get_response_pdu_size()
                        if isinstance(self.client.framer, ModbusAsciiFramer):
                            response_pdu_size = response_pdu_size * 2
                        if response_pdu_size:
                            expected_response_length = self._calculate_response_length(response_pdu_size)
                if request.unit_id in self._no_response_devices:
                    full = True
                else:
                    full = False
                c_str = str(self.client)
                if "modbusudpclient" in c_str.lower().strip():
                    full = True
                response, last_exception = self._transact(request,
                                                          expected_response_length,
                                                          full=full
                                                          )
                if not response and (
                        request.unit_id not in self._no_response_devices):
                    self._no_response_devices.append(request.unit_id)
                elif request.unit_id in self._no_response_devices:
                    self._no_response_devices.remove(request.unit_id)
                if not response and self.retry_on_empty and retries:
                    while retries > 0:
                        if hasattr(self.client, "state"):
                            _logger.debug("RESETTING Transaction state to "
                                          "'IDLE' for retry")
                            self.client.state = ModbusTransactionState.IDLE
                        _logger.debug("Retry on empty - {}".format(retries))
                        response, last_exception = self._transact(
                            request,
                            expected_response_length
                        )
                        if not response:
                            retries -= 1
                            continue
                        break
                self.client.framer.processIncomingPacket(response,
                                                         self.addTransaction,
                                                         request.unit_id)
                response = self.getTransaction(request.transaction_id)
                if not response:
                    if len(self.transactions):
                        response = self.getTransaction(tid=0)
                    else:
                        last_exception = last_exception or ("No Response received "
                                                            "from the remote unit")
                        response = ModbusIOException(last_exception)
                if hasattr(self.client, "state"):
                    _logger.debug("Changing transaction state from "
                                  "'PROCESSING REPLY' to 'TRANSCATION_COMPLETE'")
                    self.client.state = ModbusTransactionState.TRANSCATION_COMPLETE
                return response
            except Exception as ex:
                _logger.exception(ex)
                self.client.state = ModbusTransactionState.TRANSCATION_COMPLETE
                raise

    def _transact(self, packet, response_length, full=False):
        """
        Does a Write and Read transaction
        :param packet: packet to be sent
        :param response_length:  Expected response length
        :param full: the target device was notorious for its no response. Dont
            waste time this time by partial querying
        :return: response
        """
        last_exception = None
        try:
            self.client.connect()
            packet = self.client.framer.buildPacket(packet)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug("SEND: " + hexlify_packets(packet))
            size = self._send(packet)
            if size:
                _logger.debug("Changing transaction state from 'SENDING' "
                              "to 'WAITING FOR REPLY'")
                self.client.state = ModbusTransactionState.WAITING_FOR_REPLY
            result = self._recv(response_length, full)
            if _logger.isEnabledFor(logging.DEBUG):
                _logger.debug("RECV: " + hexlify_packets(result))
        except (socket.error, ModbusIOException,
                InvalidMessageReceivedException) as msg:
            self.client.close()
            _logger.debug("Transaction failed. (%s) " % msg)
            last_exception = msg
            result = b''
        return result, last_exception

    def _send(self, packet):
        return self.client.framer.sendPacket(packet)

    def _recv(self, expected_response_length, full):
        if not full:
            exception_length = self._calculate_exception_length()
            if isinstance(self.client.framer, ModbusSocketFramer):
                min_size = 8
            elif isinstance(self.client.framer, ModbusRtuFramer):
                min_size = 2
            elif isinstance(self.client.framer, ModbusAsciiFramer):
                min_size = 5
            elif isinstance(self.client.framer, ModbusBinaryFramer):
                min_size = 3
            else:
                min_size = expected_response_length

            read_min = self.client.framer.recvPacket(min_size)
            if not read_min:
                return read_min

            if len(read_min) < min_size:
                raise InvalidMessageReceivedException(
                    "Incomplete message received, expected at least %d bytes (%d received)"
                    % (min_size, len(read_min)))

            if isinstance(self.client.framer, ModbusSocketFramer):
                func_code = byte2int(read_min[-1])
            elif isinstance(self.client.framer, ModbusRtuFramer):
                func_code = byte2int(read_min[-1])
            elif isinstance(self.client.framer, ModbusAsciiFramer):
                func_code = int(read_min[3:5], 16)
            elif isinstance(self.client.framer, ModbusBinaryFramer):
                func_code = byte2int(read_min[-1])
            else:
                func_code = -1

            if func_code < 0x80:    # Not an error
                if isinstance(self.client.framer, ModbusSocketFramer):
                    # Ommit UID, which is included in header size
                    h_size = self.client.framer._hsize
                    length = struct.unpack(">H", read_min[4:6])[0] - 1
                    expected_response_length = h_size + length
                expected_response_length -= min_size
                total = expected_response_length + min_size
            else:
                expected_response_length = exception_length - min_size
                total = expected_response_length + min_size

        else:
            read_min = b''
            total = expected_response_length
        result = self.client.framer.recvPacket(expected_response_length)
        result = read_min + result
        actual = len(result)
        if actual != total:
            _logger.debug("Incomplete message received, "
                          "Expected {} bytes Recieved "
                          "{} bytes !!!!".format(total, actual))
            raise InvalidMessageReceivedException(
                "Incomplete message received, %d bytes expected (%d received)"
                % (total, actual))
        if self.client.state != ModbusTransactionState.PROCESSING_REPLY:
            _logger.debug("Changing transaction state from "
                          "'WAITING FOR REPLY' to 'PROCESSING REPLY'")
            self.client.state = ModbusTransactionState.PROCESSING_REPLY
        return result

    def addTransaction(self, request, tid=None):
        ''' Adds a transaction to the handler

        This holds the requets in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        '''
        raise NotImplementedException("addTransaction")

    def getTransaction(self, tid):
        ''' Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        '''
        raise NotImplementedException("getTransaction")

    def delTransaction(self, tid):
        ''' Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        '''
        raise NotImplementedException("delTransaction")

    def getNextTID(self):
        ''' Retrieve the next unique transaction identifier

        This handles incrementing the identifier after
        retrieval

        :returns: The next unique transaction identifier
        '''
        self.tid = (self.tid + 1) & 0xffff
        return self.tid

    def reset(self):
        ''' Resets the transaction identifier '''
        self.tid = Defaults.TransactionId
        self.transactions = type(self.transactions)()


class DictTransactionManager(ModbusTransactionManager):
    ''' Impelements a transaction for a manager where the
    results are keyed based on the supplied transaction id.
    '''

    def __init__(self, client, **kwargs):
        ''' Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        '''
        self.transactions = {}
        super(DictTransactionManager, self).__init__(client, **kwargs)

    def __iter__(self):
        ''' Iterater over the current managed transactions

        :returns: An iterator of the managed transactions
        '''
        return iterkeys(self.transactions)

    def addTransaction(self, request, tid=None):
        ''' Adds a transaction to the handler

        This holds the requets in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        '''
        tid = tid if tid != None else request.transaction_id
        _logger.debug("Adding transaction %d" % tid)
        self.transactions[tid] = request

    def getTransaction(self, tid):
        ''' Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        '''
        _logger.debug("Getting transaction %d" % tid)
        return self.transactions.pop(tid, None)

    def delTransaction(self, tid):
        ''' Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        '''
        _logger.debug("Deleting transaction %d" % tid)
        self.transactions.pop(tid, None)


class FifoTransactionManager(ModbusTransactionManager):
    ''' Impelements a transaction for a manager where the
    results are returned in a FIFO manner.
    '''

    def __init__(self, client, **kwargs):
        ''' Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        '''
        super(FifoTransactionManager, self).__init__(client, **kwargs)
        self.transactions = []

    def __iter__(self):
        ''' Iterater over the current managed transactions

        :returns: An iterator of the managed transactions
        '''
        return iter(self.transactions)

    def addTransaction(self, request, tid=None):
        ''' Adds a transaction to the handler

        This holds the requets in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        '''
        tid = tid if tid != None else request.transaction_id
        _logger.debug("Adding transaction %d" % tid)
        self.transactions.append(request)

    def getTransaction(self, tid):
        ''' Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        '''
        _logger.debug("Getting transaction %s" % str(tid))
        return self.transactions.pop(0) if self.transactions else None

    def delTransaction(self, tid):
        ''' Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        '''
        _logger.debug("Deleting transaction %d" % tid)
        if self.transactions: self.transactions.pop(0)


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    "FifoTransactionManager",
    "DictTransactionManager",
    "ModbusSocketFramer", "ModbusRtuFramer",
    "ModbusAsciiFramer", "ModbusBinaryFramer",
]
