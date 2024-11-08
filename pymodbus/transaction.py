"""Collection of transaction based abstractions."""
from __future__ import annotations


__all__ = [
    "ModbusTransactionManager",
    "SyncModbusTransactionManager",
]

from threading import RLock
from typing import TYPE_CHECKING

from pymodbus.exceptions import (
    ModbusIOException,
)
from pymodbus.framer import (
    FramerSocket,
)
from pymodbus.logging import Log
from pymodbus.pdu import ModbusPDU
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
        while True:
            if not (data := self.client.recv(None)):
                return None
            self.databuffer += data
            used_len, pdu = self.client.framer.processIncomingFrame(self.databuffer)
            self.databuffer = self.databuffer[used_len:]
            if pdu:
                return pdu

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
            exp_txt = ""
            while retry > 0:
                if not self.send_request(request):
                    Log.debug('Changing transaction state from "SENDING" to "RETRYING"')
                    exp_txt = 'SEND failed'
                    Log.error(exp_txt + ', retrying')
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
                Log.debug('Changing transaction state from "SENDING" to "WAITING_FOR_REPLY"')
                self.client.state = ModbusTransactionState.WAITING_FOR_REPLY
                if not (pdu := self.receive_response()):
                    Log.debug('Changing transaction state from "WAITING_FOR_REPLY" to "RETRYING"')
                    exp_txt = 'RECEIVE failed'
                    Log.error(exp_txt + ', retrying')
                    self.client.state = ModbusTransactionState.RETRYING
                    retry -= 1
                    continue

                print(pdu)
                break

            if not retry:
                return ModbusIOException(exp_txt, request.function_code)

            if pdu:
                self.addTransaction(pdu)
            if not (result := self.getTransaction(request.transaction_id)):
                if len(self.transactions):
                    result = self.getTransaction(0)
                else:
                    last_exception = (
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
