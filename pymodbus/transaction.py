"""Collection of transaction based abstractions."""
# pylint: disable=missing-type-doc
import socket
import struct
import time
from functools import partial
from threading import RLock

from pymodbus.constants import Defaults
from pymodbus.exceptions import (
    InvalidMessageReceivedException,
    ModbusIOException,
    NotImplementedException,
)
from pymodbus.framer.ascii_framer import ModbusAsciiFramer
from pymodbus.framer.binary_framer import ModbusBinaryFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.framer.tls_framer import ModbusTlsFramer
from pymodbus.logging import Log
from pymodbus.utilities import ModbusTransactionState, hexlify_packets


# --------------------------------------------------------------------------- #
# The Global Transaction Manager
# --------------------------------------------------------------------------- #
class ModbusTransactionManager:
    """Implement a transaction for a manager.

    The transaction protocol can be represented by the following pseudo code::

        count = 0
        do
          result = send(message)
          if (timeout or result == bad)
             count++
          else break
        while (count < 3)

    This module helps to abstract this away from the framer and protocol.
    """

    def __init__(self, client, **kwargs):
        """Initialize an instance of the ModbusTransactionManager.

        :param client: The client socket wrapper
        :param retry_on_empty: Should the client retry on empty
        :param retries: The number of retries to allow
        """
        self.tid = Defaults.TransactionId
        self.client = client
        self.backoff = kwargs.get("backoff", Defaults.Backoff) or 0.3
        self.retry_on_empty = kwargs.get("retry_on_empty", Defaults.RetryOnEmpty)
        self.retry_on_invalid = kwargs.get("retry_on_invalid", Defaults.RetryOnInvalid)
        self.retries = kwargs.get("retries", Defaults.Retries) or 1
        self.reset_socket = kwargs.get("reset_socket", True)
        self._transaction_lock = RLock()
        self._no_response_devices = []
        if client:
            self._set_adu_size()

    def _set_adu_size(self):
        """Set adu size."""
        # base ADU size of modbus frame in bytes
        if isinstance(self.client.framer, ModbusSocketFramer):
            self.base_adu_size = 7  # tid(2), pid(2), length(2), uid(1)
        elif isinstance(self.client.framer, ModbusRtuFramer):
            self.base_adu_size = 3  # address(1), CRC(2)
        elif isinstance(self.client.framer, ModbusAsciiFramer):
            self.base_adu_size = 7  # start(1)+ Address(2), LRC(2) + end(2)
        elif isinstance(self.client.framer, ModbusBinaryFramer):
            self.base_adu_size = 5  # start(1) + Address(1), CRC(2) + end(1)
        elif isinstance(self.client.framer, ModbusTlsFramer):
            self.base_adu_size = 0  # no header and footer
        else:
            self.base_adu_size = -1

    def _calculate_response_length(self, expected_pdu_size):
        """Calculate response length."""
        if self.base_adu_size == -1:
            return None
        return self.base_adu_size + expected_pdu_size

    def _calculate_exception_length(self):
        """Return the length of the Modbus Exception Response according to the type of Framer."""
        if isinstance(self.client.framer, (ModbusSocketFramer, ModbusTlsFramer)):
            return self.base_adu_size + 2  # Fcode(1), ExceptionCode(1)
        if isinstance(self.client.framer, ModbusAsciiFramer):
            return self.base_adu_size + 4  # Fcode(2), ExceptionCode(2)
        if isinstance(self.client.framer, (ModbusRtuFramer, ModbusBinaryFramer)):
            return self.base_adu_size + 2  # Fcode(1), ExceptionCode(1)
        return None

    def _validate_response(self, request, response, exp_resp_len):
        """Validate Incoming response against request.

        :param request: Request sent
        :param response: Response received
        :param exp_resp_len: Expected response length
        :return: New transactions state
        """
        if not response:
            return False

        mbap = self.client.framer.decode_data(response)
        if (
            mbap.get("unit") != request.unit_id
            or mbap.get("fcode") & 0x7F != request.function_code
        ):
            return False

        if "length" in mbap and exp_resp_len:
            return mbap.get("length") == exp_resp_len
        return True

    def execute(self, request):  # pylint: disable=too-complex
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        with self._transaction_lock:
            try:
                Log.debug(
                    "Current transaction state - {}",
                    ModbusTransactionState.to_string(self.client.state),
                )
                retries = self.retries
                request.transaction_id = self.getNextTID()
                Log.debug("Running transaction {}", request.transaction_id)
                if _buffer := hexlify_packets(
                    self.client.framer._buffer  # pylint: disable=protected-access
                ):
                    Log.debug("Clearing current Frame: - {}", _buffer)
                    self.client.framer.resetFrame()
                if broadcast := (
                    self.client.params.broadcast_enable and not request.unit_id
                ):
                    self._transact(request, None, broadcast=True)
                    response = b"Broadcast write sent - no response expected"
                else:
                    expected_response_length = None
                    if not isinstance(self.client.framer, ModbusSocketFramer):
                        if hasattr(request, "get_response_pdu_size"):
                            response_pdu_size = request.get_response_pdu_size()
                            if isinstance(self.client.framer, ModbusAsciiFramer):
                                response_pdu_size = response_pdu_size * 2
                            if response_pdu_size:
                                expected_response_length = (
                                    self._calculate_response_length(response_pdu_size)
                                )
                    if (  # pylint: disable=simplifiable-if-statement
                        request.unit_id in self._no_response_devices
                    ):
                        full = True
                    else:
                        full = False
                    c_str = str(self.client)
                    if "modbusudpclient" in c_str.lower().strip():
                        full = True
                        if not expected_response_length:
                            expected_response_length = Defaults.ReadSize
                    response, last_exception = self._transact(
                        request,
                        expected_response_length,
                        full=full,
                        broadcast=broadcast,
                    )
                    while retries > 0:
                        valid_response = self._validate_response(
                            request, response, expected_response_length
                        )
                        if valid_response:
                            if (
                                request.unit_id in self._no_response_devices
                                and response
                            ):
                                self._no_response_devices.remove(request.unit_id)
                                Log.debug("Got response!!!")
                            break
                        if not response:
                            if request.unit_id not in self._no_response_devices:
                                self._no_response_devices.append(request.unit_id)
                            if self.retry_on_empty:
                                response, last_exception = self._retry_transaction(
                                    retries,
                                    "empty",
                                    request,
                                    expected_response_length,
                                    full=full,
                                )
                                retries -= 1
                            else:
                                # No response received and retries not enabled
                                break
                        elif self.retry_on_invalid:
                            response, last_exception = self._retry_transaction(
                                retries,
                                "invalid",
                                request,
                                expected_response_length,
                                full=full,
                            )
                            retries -= 1
                        else:
                            break
                        # full = False
                    addTransaction = partial(  # pylint: disable=invalid-name
                        self.addTransaction,
                        tid=request.transaction_id,
                    )
                    self.client.framer.processIncomingPacket(
                        response, addTransaction, request.unit_id
                    )
                    if not (response := self.getTransaction(request.transaction_id)):
                        if len(self.transactions):
                            response = self.getTransaction(tid=0)
                        else:
                            last_exception = last_exception or (
                                "No Response received from the remote unit"
                                "/Unable to decode response"
                            )
                            response = ModbusIOException(
                                last_exception, request.function_code
                            )
                        if self.reset_socket:
                            self.client.close()
                    if hasattr(self.client, "state"):
                        Log.debug(
                            "Changing transaction state from "
                            '"PROCESSING REPLY" to '
                            '"TRANSACTION_COMPLETE"'
                        )
                        self.client.state = ModbusTransactionState.TRANSACTION_COMPLETE

                return response
            except ModbusIOException as exc:
                # Handle decode errors in processIncomingPacket method
                Log.error("Modbus IO exception {}", exc)
                self.client.state = ModbusTransactionState.TRANSACTION_COMPLETE
                if self.reset_socket:
                    self.client.close()
                return exc

    def _retry_transaction(self, retries, reason, packet, response_length, full=False):
        """Retry transaction."""
        Log.debug("Retry on {} response - {}", reason, retries)
        Log.debug('Changing transaction state from "WAITING_FOR_REPLY" to "RETRYING"')
        self.client.state = ModbusTransactionState.RETRYING
        if self.backoff:
            delay = 2 ** (self.retries - retries) * self.backoff
            time.sleep(delay)
            Log.debug("Sleeping {}", delay)
        self.client.connect()
        if hasattr(self.client, "_in_waiting"):
            if (
                in_waiting := self.client._in_waiting()  # pylint: disable=protected-access
            ):
                if response_length == in_waiting:
                    result = self._recv(response_length, full)
                    return result, None
        return self._transact(packet, response_length, full=full)

    def _transact(self, packet, response_length, full=False, broadcast=False):
        """Do a Write and Read transaction.

        :param packet: packet to be sent
        :param response_length:  Expected response length
        :param full: the target device was notorious for its no response. Dont
            waste time this time by partial querying
        :param broadcast:
        :return: response
        """
        last_exception = None
        try:
            self.client.connect()
            packet = self.client.framer.buildPacket(packet)
            Log.debug("SEND: {}", packet, ":hex")
            size = self._send(packet)
            if (
                isinstance(size, bytes)
                and self.client.state == ModbusTransactionState.RETRYING
            ):
                Log.debug(
                    "Changing transaction state from "
                    '"RETRYING" to "PROCESSING REPLY"'
                )
                self.client.state = ModbusTransactionState.PROCESSING_REPLY
                return size, None
            if broadcast:
                if size:
                    Log.debug(
                        'Changing transaction state from "SENDING" '
                        'to "TRANSACTION_COMPLETE"'
                    )
                    self.client.state = ModbusTransactionState.TRANSACTION_COMPLETE
                return b"", None
            if size:
                Log.debug(
                    'Changing transaction state from "SENDING" '
                    'to "WAITING FOR REPLY"'
                )
                self.client.state = ModbusTransactionState.WAITING_FOR_REPLY
            if (
                hasattr(self.client, "handle_local_echo")
                and self.client.handle_local_echo is True
            ):
                if self._recv(size, full) != packet:
                    return b"", "Wrong local echo"
            result = self._recv(response_length, full)
            # result2 = self._recv(response_length, full)
            Log.debug("RECV: {}", result, ":hex")
        except (
            socket.error,
            ModbusIOException,
            InvalidMessageReceivedException,
        ) as msg:
            if self.reset_socket:
                self.client.close()
            Log.debug("Transaction failed. ({}) ", msg)
            last_exception = msg
            result = b""
        return result, last_exception

    def _send(self, packet, retrying=False):  # pylint: disable=unused-argument
        """Send."""
        return self.client.framer.sendPacket(packet)

    def _recv(self, expected_response_length, full):  # pylint: disable=too-complex
        """Receive."""
        total = None
        if not full:
            exception_length = self._calculate_exception_length()
            if isinstance(self.client.framer, ModbusSocketFramer):
                min_size = 8
            elif isinstance(self.client.framer, ModbusRtuFramer):
                min_size = 4
            elif isinstance(self.client.framer, ModbusAsciiFramer):
                min_size = 5
            elif isinstance(self.client.framer, ModbusBinaryFramer):
                min_size = 3
            else:
                min_size = expected_response_length

            read_min = self.client.framer.recvPacket(min_size)
            if len(read_min) != min_size:
                msg_start = "Incomplete message" if read_min else "No response"
                raise InvalidMessageReceivedException(
                    f"{msg_start} received, expected at least {min_size} bytes "
                    f"({len(read_min)} received)"
                )
            if read_min:
                if isinstance(self.client.framer, ModbusSocketFramer):
                    func_code = int(read_min[-1])
                elif isinstance(self.client.framer, ModbusRtuFramer):
                    func_code = int(read_min[1])
                elif isinstance(self.client.framer, ModbusAsciiFramer):
                    func_code = int(read_min[3:5], 16)
                elif isinstance(self.client.framer, ModbusBinaryFramer):
                    func_code = int(read_min[-1])
                else:
                    func_code = -1

                if func_code < 0x80:  # Not an error
                    if isinstance(self.client.framer, ModbusSocketFramer):
                        # Omit UID, which is included in header size
                        h_size = (
                            self.client.framer._hsize  # pylint: disable=protected-access
                        )
                        length = struct.unpack(">H", read_min[4:6])[0] - 1
                        expected_response_length = h_size + length
                    elif expected_response_length is None and isinstance(
                        self.client.framer, ModbusRtuFramer
                    ):
                        try:
                            expected_response_length = (
                                self.client.framer.get_expected_response_length(
                                    read_min
                                )
                            )
                        except IndexError:
                            # Could not determine response length with available bytes
                            pass
                    if expected_response_length is not None:
                        expected_response_length -= min_size
                        total = expected_response_length + min_size
                else:
                    expected_response_length = exception_length - min_size
                    total = expected_response_length + min_size
            else:
                total = expected_response_length
        else:
            read_min = b""
            total = expected_response_length
        result = self.client.framer.recvPacket(expected_response_length)
        result = read_min + result
        actual = len(result)
        if total is not None and actual != total:
            msg_start = "Incomplete message" if actual else "No response"
            Log.debug(
                "{} received, Expected {} bytes Received {} bytes !!!!",
                msg_start,
                total,
                actual,
            )
        elif not actual:
            # If actual == 0 and total is not None then the above
            # should be triggered, so total must be None here
            Log.debug("No response received to unbounded read !!!!")
        if self.client.state != ModbusTransactionState.PROCESSING_REPLY:
            Log.debug(
                "Changing transaction state from "
                '"WAITING FOR REPLY" to "PROCESSING REPLY"'
            )
            self.client.state = ModbusTransactionState.PROCESSING_REPLY
        return result

    def addTransaction(self, request, tid=None):  # pylint: disable=invalid-name
        """Add a transaction to the handler.

        This holds the request in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        :raises NotImplementedException:
        """
        raise NotImplementedException("addTransaction")

    def getTransaction(self, tid):  # pylint: disable=invalid-name
        """Return a transaction matching the referenced tid.

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        :raises NotImplementedException:
        """
        raise NotImplementedException("getTransaction")

    def delTransaction(self, tid):  # pylint: disable=invalid-name
        """Remove a transaction matching the referenced tid.

        :param tid: The transaction to remove
        :raises NotImplementedException:
        """
        raise NotImplementedException("delTransaction")

    def getNextTID(self):  # pylint: disable=invalid-name
        """Retrieve the next unique transaction identifier.

        This handles incrementing the identifier after
        retrieval

        :returns: The next unique transaction identifier
        """
        self.tid = (self.tid + 1) & 0xFFFF
        return self.tid

    def reset(self):
        """Reset the transaction identifier."""
        self.tid = Defaults.TransactionId
        self.transactions = type(  # pylint: disable=attribute-defined-outside-init
            self.transactions
        )()


class DictTransactionManager(ModbusTransactionManager):
    """Implements a transaction for a manager.

    Where the results are keyed based on the supplied transaction id.
    """

    def __init__(self, client, **kwargs):
        """Initialize an instance of the ModbusTransactionManager.

        :param client: The client socket wrapper
        """
        self.transactions = {}
        super().__init__(client, **kwargs)

    def __iter__(self):
        """Iterate over the current managed transactions.

        :returns: An iterator of the managed transactions
        """
        return iter(self.transactions.keys())

    def addTransaction(self, request, tid=None):
        """Add a transaction to the handler.

        This holds the requests in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        """
        tid = tid if tid is not None else request.transaction_id
        Log.debug("Adding transaction {}", tid)
        self.transactions[tid] = request

    def getTransaction(self, tid):
        """Return a transaction matching the referenced tid.

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve

        """
        Log.debug("Getting transaction {}", tid)
        if not tid:
            if self.transactions:
                return self.transactions.popitem()[1]
            return None
        return self.transactions.pop(tid, None)

    def delTransaction(self, tid):
        """Remove a transaction matching the referenced tid.

        :param tid: The transaction to remove
        """
        Log.debug("deleting transaction {}", tid)
        self.transactions.pop(tid, None)


class FifoTransactionManager(ModbusTransactionManager):
    """Implements a transaction.

    For a manager where the results are returned in a FIFO manner.
    """

    def __init__(self, client, **kwargs):
        """Initialize an instance of the ModbusTransactionManager.

        :param client: The client socket wrapper
        """
        super().__init__(client, **kwargs)
        self.transactions = []

    def __iter__(self):
        """Iterate over the current managed transactions.

        :returns: An iterator of the managed transactions
        """
        return iter(self.transactions)

    def addTransaction(self, request, tid=None):
        """Add a transaction to the handler.

        This holds the requests in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        """
        tid = tid if tid is not None else request.transaction_id
        Log.debug("Adding transaction {}", tid)
        self.transactions.append(request)

    def getTransaction(self, tid):
        """Return a transaction matching the referenced tid.

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        """
        return self.transactions.pop(0) if self.transactions else None

    def delTransaction(self, tid):
        """Remove a transaction matching the referenced tid.

        :param tid: The transaction to remove
        """
        Log.debug("Deleting transaction {}", tid)
        if self.transactions:
            self.transactions.pop(0)


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = [
    "FifoTransactionManager",
    "DictTransactionManager",
    "ModbusSocketFramer",
    "ModbusTlsFramer",
    "ModbusRtuFramer",
    "ModbusAsciiFramer",
    "ModbusBinaryFramer",
]
