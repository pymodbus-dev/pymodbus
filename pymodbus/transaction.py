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
from pymodbus.pdu import ExceptionResponse, ModbusPDU
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
    """Implement a transaction for a manager."""

    def __init__(self, client: ModbusBaseSyncClient, retries):
        """Initialize an instance of the ModbusTransactionManager."""
        super().__init__()
        self.client: ModbusBaseSyncClient = client
        self.retries = retries
        self._transaction_lock = RLock()
        self.databuffer = b''

    def send_request(self, request: ModbusPDU) -> bool:
        """Build and send request."""
        self.client.connect()
        packet = self.client.framer.buildFrame(request)
        Log.debug("SEND: {}", packet, ":hex")
        if (size := self.client.send(packet)) != len(packet):
            Log.error(f"Only sent {size} of {len(packet)} bytes")
            return False
        if self.client.comm_params.handle_local_echo and self.client.recv(size) != packet:
            Log.error("Wrong local echo")
            return False
        return True

    def receive_response(self) -> ModbusPDU | None:
        """Receive until PDU is correct or timeout."""
        return None

    def execute(self, no_response_expected: bool, request: ModbusPDU):  # noqa: C901
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        with self._transaction_lock:
            Log.debug(
                "Current transaction state - {}",
                ModbusTransactionState.to_string(self.client.state),
            )
            if isinstance(self.client.framer, FramerSocket):
                request.transaction_id = self.getNextTID()
            else:
                request.transaction_id = 0
            Log.debug("Running transaction {}", request.transaction_id)
            if _buffer := hexlify_packets(
                self.databuffer
            ):
                Log.debug("Clearing current Frame: - {}", _buffer)
                self.databuffer = b''

            retry = self.retries + 1
            while retry > 0:
                if not self.send_request(request):
                    Log.debug('Changing transaction state from SENDING to "RETRYING"')
                    Log.error('SEND failed, retrying')
                    self.client.state = ModbusTransactionState.RETRYING
                    retry -= 1
                    continue
                if no_response_expected:
                    Log.debug(
                        'Changing transaction state from "SENDING" '
                        'to "TRANSACTION_COMPLETE" (no response expected)'
                    )
                    self.client.state = ModbusTransactionState.TRANSACTION_COMPLETE
                    return None

                break

            if not retry:
                return ModbusIOException("SEND failed", request.function_code)

            try:
                expected_response_length = None
                if not isinstance(self.client.framer, FramerSocket):
                    response_pdu_size = request.get_response_pdu_size()
                    if isinstance(self.client.framer, FramerAscii):
                        response_pdu_size *= 2
                    if response_pdu_size:
                        expected_response_length = self.client.framer.MIN_SIZE + response_pdu_size -1
                response, last_exception = self._transact(expected_response_length)
                if no_response_expected:
                    return None
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

    def _transact(self, response_length):
        """Do a Write and Read transaction."""
        try:
            state = '"RETRYING"' if self.client.state == ModbusTransactionState.RETRYING else '"SENDING"'
            Log.debug(f'Changing transaction state from {state} to "WAITING FOR REPLY"')
            self.client.state = ModbusTransactionState.WAITING_FOR_REPLY
            result = self._recv(response_length)
            Log.debug("RECV: {}", result, ":hex")
            return result, None
        except (OSError, ModbusIOException, InvalidMessageReceivedException, ConnectionException) as msg:
            self.client.close()
            Log.debug("Transaction failed. ({}) ", msg)
            return b"", msg

    def _recv(self, expected_response_length) -> bytes:  # noqa: C901
        """Receive."""
        if self.client.comm_params.comm_type == CommType.UDP:
            read_min = self.client.recv(500)
        else:
            read_min = self.client.recv(self.client.framer.MIN_SIZE)
        if (min_size := len(read_min)) < self.client.framer.MIN_SIZE:
            msg_start = "Incomplete message" if read_min else "No response"
            raise InvalidMessageReceivedException(
                f"{msg_start} received, expected at least {self.client.framer.MIN_SIZE} bytes "
                f"({min_size} received)"
            )

        if isinstance(self.client.framer, (FramerSocket, FramerTLS)):
            func_code = int(read_min[self.client.framer.MIN_SIZE-1])
        elif isinstance(self.client.framer, FramerRTU):
            func_code = int(read_min[1])
        elif isinstance(self.client.framer, FramerAscii):
            func_code = int(read_min[3:5], 16)
        else:
            func_code = -1

        total = None
        if func_code < 0x80:  # Not an error
            if isinstance(self.client.framer, (FramerSocket, FramerTLS)):
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
            if isinstance(self.client.framer, FramerAscii):
                total = self.client.framer.MIN_SIZE + 2  # ExceptionCode(2)
            else:
                total = self.client.framer.MIN_SIZE + 1  # ExceptionCode(1)
            expected_response_length = total - min_size
        result = read_min

        if total and (missing_len := total - min_size):
            retries = 0
            while missing_len and retries < self.retries:
                if retries:
                    time.sleep(0.1)
                data = self.client.recv(missing_len)
                result += data
                missing_len -= len(data)
                retries += 1

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
        if not (pdu_class := self.client.framer.decoder.lookupPduClass(data)):
            pdu_class = ExceptionResponse
        return pdu_class.calculateRtuFrameSize(data)
