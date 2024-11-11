"""Collection of transaction based abstractions."""
from __future__ import annotations

import asyncio
from collections.abc import Callable

from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.framer import FramerBase
from pymodbus.logging import Log
from pymodbus.pdu import ModbusPDU
from pymodbus.transport import CommParams, ModbusProtocol


class TransactionManager(ModbusProtocol):
    """Transaction manager.

    This is the central class of the library, providing a separation between API and communication:

    - clients/servers calls the manager to execute requests/responses
    - transport/framer/pdu is by the manager to communicate with the devices

    Transaction manager handles:
    - Execution of requests (client), with retries and locking
    - Sending of responses (server), with retries
    - Connection management (on top of what transport offers)
    - No response (temporarily) from a device

    Transaction manager offers:
    - a simple execute interface for requests (client)
    - a simple send interface for responses (server)
    - external trace methods tracing:
        - outgoing/incoming packets (byte stream)
        - outgoing/incoming PDUs
    """

    def __init__(
        self,
        params: CommParams,
        framer: FramerBase,
        retries: int,
        is_server: bool,
        ) -> None:
        """Initialize an instance of the ModbusTransactionManager."""
        super().__init__(params, is_server)
        self.framer = framer
        self.retries = retries
        self.next_tid: int = 0
        self.trace_recv_packet: Callable[[bytes | None], bytes] | None = None
        self.trace_recv_pdu: Callable[[ModbusPDU | None], ModbusPDU] | None = None
        self.trace_send_packet: Callable[[bytes | None], bytes] | None = None
        self.trace_send_pdu: Callable[[ModbusPDU | None], ModbusPDU] | None = None
        self.accept_no_response_limit = retries + 3
        self.count_no_responses = 0
        self._lock = asyncio.Lock()
        self.response_future: asyncio.Future = asyncio.Future()

    async def execute(self, no_response_expected: bool, request) -> ModbusPDU | None:
        """Execute requests asynchronously."""
        if not self.transport:
            Log.warning("Not connected, trying to connect!")
            if not await self.connect():
                raise ConnectionException("Client cannot connect (automatic retry continuing) !!")
        async with self._lock:
            request.transaction_id = self.getNextTID()
            if self.trace_send_pdu:
                request = self.trace_send_pdu(request)  # pylint: disable=not-callable
            packet = self.framer.buildFrame(request)
            count_retries = 0
            while count_retries <= self.retries:
                if self.trace_send_packet:
                    packet = self.trace_send_packet(packet)  # pylint: disable=not-callable
                self.send(packet)
                if no_response_expected:
                    return None
                try:
                    response = await asyncio.wait_for(
                        self.response_future, timeout=self.comm_params.timeout_connect
                    )
                    self.count_no_responses = 0
                    self.response_future = asyncio.Future()
                    self.response_future = asyncio.Future()
                    return response
                except asyncio.exceptions.TimeoutError:
                    count_retries += 1
            if self.count_no_responses >= self.accept_no_response_limit:
                self.connection_lost(asyncio.TimeoutError("Server not responding"))
                raise ModbusIOException(
                    f"ERROR: No response received of the last {self.accept_no_response_limit} request, CLOSING CONNECTION."
                )
            self.count_no_responses += 1
            Log.error(f"No response received after {self.retries} retries, continue with next request")
            self.response_future = asyncio.Future()
            return None

    def callback_new_connection(self):
        """Call when listener receive new connection request."""

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""
        self.count_no_responses = 0
        self.next_tid = 0

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""
        if self.trace_recv_packet:
            self.trace_recv_packet(None)  # pylint: disable=not-callable
        if self.trace_recv_pdu:
            self.trace_recv_pdu(None)  # pylint: disable=not-callable
        if self.trace_send_packet:
            self.trace_send_packet(None)  # pylint: disable=not-callable
        if self.trace_send_pdu:
            self.trace_send_pdu(None)  # pylint: disable=not-callable

    def callback_data(self, data: bytes, _addr: tuple | None = None) -> int:
        """Handle received data."""
        if self.trace_recv_packet:
            data = self.trace_recv_packet(data)  # pylint: disable=not-callable
        used_len, pdu = self.framer.processIncomingFrame(data)
        if pdu:
            if self.trace_recv_pdu:
                pdu = self.trace_recv_pdu(pdu)  # pylint: disable=not-callable
            self.response_future.set_result(pdu)
        return used_len

    def getNextTID(self) -> int:
        """Retrieve the next transaction identifier."""
        if self.next_tid >= 65000:
            self.next_tid = 1
        else:
            self.next_tid += 1
        return self.next_tid
