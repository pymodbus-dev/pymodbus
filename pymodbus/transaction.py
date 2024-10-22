"""Collection of transaction based abstractions."""
from __future__ import annotations


__all__ = [
    "ModbusTransactionManager",
    "SyncModbusTransactionManager",
]

import struct
import time
from contextlib import suppress
from threading import RLock
from typing import TYPE_CHECKING

from pymodbus.exceptions import (
    ConnectionException,
    InvalidMessageReceivedException,
    ModbusIOException,
)
from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
    FramerTLS,
)
from pymodbus.logging import Log
from pymodbus.pdu import ModbusPDU
from pymodbus.transport import CommType
from pymodbus.utilities import ModbusTransactionState, hexlify_packets


if TYPE_CHECKING:
    from pymodbus.client.base import ModbusBaseSyncClient


# --------------------------------------------------------------------------- #
# The Global Transaction Manager
# --------------------------------------------------------------------------- #
class ModbusTransactionManager:
    """Implement a transaction for a manager.

    Results are keyed based on the supplied transaction id.
    """

    def __init__(self):
        """Initialize an instance of the ModbusTransactionManager."""
        self.tid = 0
        self.transactions: dict[int, ModbusPDU] = {}

    def __iter__(self):
        """Iterate over the current managed transactions.

        :returns: An iterator of the managed transactions
        """
        return iter(self.transactions.keys())

    def addTransaction(self, request: ModbusPDU):
        """Add a transaction to the handler.

        This holds the request in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        """
        tid = request.transaction_id
        Log.debug("Adding transaction {}", tid)
        self.transactions[tid] = request

    def getTransaction(self, tid: int):
        """Return a transaction matching the referenced tid.

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve

        """
        Log.debug("Getting transaction {}", tid)
        if not tid:
            if self.transactions:
                ret = self.transactions.popitem()[1]
                self.transactions.clear()
                return ret
            return None
        return self.transactions.pop(tid, None)

    def delTransaction(self, tid: int):
        """Remove a transaction matching the referenced tid.

        :param tid: The transaction to remove
        """
        Log.debug("deleting transaction {}", tid)
        self.transactions.pop(tid, None)

    def getNextTID(self) -> int:
        """Retrieve the next unique transaction identifier.

        This handles incrementing the identifier after
        retrieval

        :returns: The next unique transaction identifier
        """
        if self.tid < 65000:
            self.tid += 1
        else:
            self.tid = 1
        return self.tid

    def reset(self):
        """Reset the transaction identifier."""
        self.tid = 0
        self.transactions = {}


class SyncModbusTransactionManager(ModbusTransactionManager):
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

    Results are keyed based on the supplied transaction id.
    """

    def __init__(self, client: ModbusBaseSyncClient, retries):
        """Initialize an instance of the ModbusTransactionManager."""
        super().__init__()
        self.client: ModbusBaseSyncClient = client
        self.retries = retries
        self._transaction_lock = RLock()
        self._no_response_devices: list[int] = []
        self.databuffer = b''
        if client:
            self._set_adu_size()

    def _set_adu_size(self):
        """Set adu size."""
        # base ADU size of modbus frame in bytes
        if isinstance(self.client.framer, FramerSocket):
            self.base_adu_size = 7  # tid(2), pid(2), length(2), uid(1)
        elif isinstance(self.client.framer, FramerRTU):
            self.base_adu_size = 3  # address(1), CRC(2)
        elif isinstance(self.client.framer, FramerAscii):
            self.base_adu_size = 7  # start(1)+ Address(2), LRC(2) + end(2)
        elif isinstance(self.client.framer, FramerTLS):
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
        if isinstance(self.client.framer, (FramerSocket, FramerTLS)):
            return self.base_adu_size + 2  # Fcode(1), ExceptionCode(1)
        if isinstance(self.client.framer, FramerAscii):
            return self.base_adu_size + 4  # Fcode(2), ExceptionCode(2)
        if isinstance(self.client.framer, FramerRTU):
            return self.base_adu_size + 2  # Fcode(1), ExceptionCode(1)
        return None

    def _validate_response(self, response):
        """Validate Incoming response against request."""
        if not response:
            return False
        return True

    def execute(self, no_response_expected: bool, request: ModbusPDU):  # noqa: C901
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        with self._transaction_lock:
            try:
                Log.debug(
                    "Current transaction state - {}",
                    ModbusTransactionState.to_string(self.client.state),
                )
                retries = self.retries
                if isinstance(self.client.framer, FramerSocket):
                    request.transaction_id = self.getNextTID()
                else:
                    request.transaction_id = 0
                Log.debug("Running transaction {}", request.transaction_id)
                if _buffer := hexlify_packets(
                    self.client.framer.databuffer
                ):
                    Log.debug("Clearing current Frame: - {}", _buffer)
                    self.client.framer.databuffer = b''
                expected_response_length = None
                if not isinstance(self.client.framer, FramerSocket):
                    response_pdu_size = request.get_response_pdu_size()
                    if isinstance(self.client.framer, FramerAscii):
                        response_pdu_size *= 2
                    if response_pdu_size:
                        expected_response_length = (
                            self._calculate_response_length(response_pdu_size)
                        )
                if (  # pylint: disable=simplifiable-if-statement
                    request.slave_id in self._no_response_devices
                ):
                    full = True
                else:
                    full = False
                if self.client.comm_params.comm_type == CommType.UDP:
                    full = True
                    if not expected_response_length:
                        expected_response_length = 1024
                response, last_exception = self._transact(
                    no_response_expected,
                    request,
                    expected_response_length,
                    full=full,
                )
                if no_response_expected:
                    return None
                while retries > 0:
                    if self._validate_response(response):
                        if (
                            request.slave_id in self._no_response_devices
                            and response
                        ):
                            self._no_response_devices.remove(request.slave_id)
                            Log.debug("Got response!!!")
                        break
                    if not response:
                        if request.slave_id not in self._no_response_devices:
                            self._no_response_devices.append(request.slave_id)
                    # No response received and retries not enabled
                    break
                self.databuffer += response
                used_len, pdu = self.client.framer.processIncomingFrame(self.databuffer)
                self.databuffer = self.databuffer[used_len:]
                if pdu:
                    self.addTransaction(pdu)
                if not (result := self.getTransaction(request.transaction_id)):
                    if len(self.transactions):
                        result = self.getTransaction(0)
                    else:
                        last_exception = last_exception or (
                            "No Response received from the remote slave"
                            "/Unable to decode response"
                        )
                        result = ModbusIOException(
                            last_exception, request.function_code
                        )
                        self.client.close()
                if hasattr(self.client, "state"):
                    Log.debug(
                        "Changing transaction state from "
                        '"PROCESSING REPLY" to '
                        '"TRANSACTION_COMPLETE"'
                    )
                    self.client.state = ModbusTransactionState.TRANSACTION_COMPLETE
                return result
            except ModbusIOException as exc:
                # Handle decode errors method
                Log.error("Modbus IO exception {}", exc)
                self.client.state = ModbusTransactionState.TRANSACTION_COMPLETE
                self.client.close()
                return exc

    def _retry_transaction(self, no_response_expected, retries, reason, packet, response_length, full=False):
        """Retry transaction."""
        Log.debug("Retry on {} response - {}", reason, retries)
        Log.debug('Changing transaction state from "WAITING_FOR_REPLY" to "RETRYING"')
        self.client.state = ModbusTransactionState.RETRYING
        self.client.connect()
        if hasattr(self.client, "_in_waiting"):
            if (
                in_waiting := self.client._in_waiting()  # pylint: disable=protected-access
            ):
                if response_length == in_waiting:
                    result = self._recv(response_length, full)
                    return result, None
        return self._transact(no_response_expected, packet, response_length, full=full)

    def _transact(self, no_response_expected: bool, request: ModbusPDU, response_length, full=False):
        """Do a Write and Read transaction."""
        last_exception = None
        try:
            self.client.connect()
            packet = self.client.framer.buildFrame(request)
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
            if self.client.comm_params.handle_local_echo is True:
                if self._recv(size, full) != packet:
                    return b"", "Wrong local echo"
            if no_response_expected:
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
            result = self._recv(response_length, full)
            # result2 = self._recv(response_length, full)
            Log.debug("RECV: {}", result, ":hex")
        except (OSError, ModbusIOException, InvalidMessageReceivedException, ConnectionException) as msg:
            self.client.close()
            Log.debug("Transaction failed. ({}) ", msg)
            last_exception = msg
            result = b""
        return result, last_exception

    def _send(self, packet: bytes, _retrying=False):
        """Send."""
        return self.client.send(packet)

    def _recv(self, expected_response_length, full) -> bytes:  # noqa: C901
        """Receive."""
        total = None
        if not full:
            exception_length = self._calculate_exception_length()
            if isinstance(self.client.framer, FramerSocket):
                min_size = 8
            elif isinstance(self.client.framer, FramerRTU):
                min_size = 4
            elif isinstance(self.client.framer, FramerAscii):
                min_size = 5
            else:
                min_size = expected_response_length

            read_min = self.client.recv(min_size)
            if min_size and len(read_min) != min_size:
                msg_start = "Incomplete message" if read_min else "No response"
                raise InvalidMessageReceivedException(
                    f"{msg_start} received, expected at least {min_size} bytes "
                    f"({len(read_min)} received)"
                )
            if read_min:
                if isinstance(self.client.framer, FramerSocket):
                    func_code = int(read_min[-1])
                elif isinstance(self.client.framer, FramerRTU):
                    func_code = int(read_min[1])
                elif isinstance(self.client.framer, FramerAscii):
                    func_code = int(read_min[3:5], 16)
                else:
                    func_code = -1

                if func_code < 0x80:  # Not an error
                    if isinstance(self.client.framer, FramerSocket):
                        length = struct.unpack(">H", read_min[4:6])[0] - 1
                        expected_response_length = 7 + length
                    elif expected_response_length is None and isinstance(
                        self.client.framer, FramerRTU
                    ):
                        with suppress(
                            IndexError  # response length indeterminate with available bytes
                        ):
                            expected_response_length = (
                                self._get_expected_response_length(
                                    read_min
                                )
                            )
                    if expected_response_length is not None:
                        expected_response_length -= min_size
                        total = expected_response_length + min_size
                else:
                    expected_response_length = exception_length - min_size
                    total = expected_response_length + min_size
            else:
                total = expected_response_length
            retries = 0
            missing_len = expected_response_length
            result = read_min
            while missing_len and retries < self.retries:
                if retries:
                    time.sleep(0.1)
                data = self.client.recv(expected_response_length)
                result += data
                missing_len -= len(data)
                retries += 1
        else:
            read_min = b""
            total = expected_response_length
            result = self.client.recv(expected_response_length)
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

    def _get_expected_response_length(self, data) -> int:
        """Get the expected response length.

        :param data: Message data read so far
        :raises IndexError: If not enough data to read byte count
        :return: Total frame size
        """
        func_code = int(data[1])
        pdu_class = self.client.framer.decoder.lookupPduClass(func_code)
        return pdu_class.calculateRtuFrameSize(data)
