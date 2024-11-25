"""Collection of transaction based abstractions."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from threading import RLock

from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.framer import FramerBase
from pymodbus.logging import Log
from pymodbus.pdu import ExceptionResponse, ModbusPDU
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
        sync_client = None,
        ) -> None:
        """Initialize an instance of the ModbusTransactionManager."""
        super().__init__(params, is_server, is_sync=bool(sync_client))
        self.framer = framer
        self.retries = retries
        self.next_tid: int = 0
        self.trace_recv_packet: Callable[[bytes | None], bytes] | None = None
        self.trace_recv_pdu: Callable[[ModbusPDU | None], ModbusPDU] | None = None
        self.trace_send_packet: Callable[[bytes | None], bytes] | None = None
        self.trace_send_pdu: Callable[[ModbusPDU | None], ModbusPDU] | None = None
        self.accept_no_response_limit = retries + 3
        self.count_no_responses = 0
        if sync_client:
            self.sync_client = sync_client
            self._sync_lock = RLock()
        else:
            self._lock = asyncio.Lock()
        self.response_future: asyncio.Future = asyncio.Future()

    def sync_get_response(self) -> ModbusPDU:
        """Receive until PDU is correct or timeout."""
        databuffer = b''
        while True:
            if not (data := self.sync_client.recv(None)):
                raise asyncio.exceptions.TimeoutError()
            databuffer += data
            used_len, pdu = self.framer.processIncomingFrame(databuffer)
            databuffer = databuffer[used_len:]
            if pdu:
                return pdu

    def sync_execute(self, no_response_expected: bool, request: ModbusPDU) -> ModbusPDU:
        """Execute requests asynchronously.

        REMARK: this method is identical to execute, apart from the lock and sync_receive.
                any changes in either method MUST be mirrored !!!
        """
        if not self.transport:
            Log.warning("Not connected, trying to connect!")
            if not self.sync_client.connect():
                raise ConnectionException("Client cannot connect (automatic retry continuing) !!")
        with self._sync_lock:
            request.transaction_id = self.getNextTID()
            if self.trace_send_pdu:
                request = self.trace_send_pdu(request)  # pylint: disable=not-callable
            packet = self.framer.buildFrame(request)
            count_retries = 0
            while count_retries <= self.retries:
                if self.trace_send_packet:
                    packet = self.trace_send_packet(packet)  # pylint: disable=not-callable
                self.sync_client.send(packet)
                if no_response_expected:
                    return ExceptionResponse(0xff)
                try:
                    return self.sync_get_response()
                except asyncio.exceptions.TimeoutError:
                    count_retries += 1
            if self.count_no_responses >= self.accept_no_response_limit:
                self.connection_lost(asyncio.TimeoutError("Server not responding"))
                raise ModbusIOException(
                    f"ERROR: No response received of the last {self.accept_no_response_limit} request, CLOSING CONNECTION."
                )
            self.count_no_responses += 1
            txt = f"No response received after {self.retries} retries, continue with next request"
            Log.error(txt)
            raise ModbusIOException(txt)

    async def execute(self, no_response_expected: bool, request: ModbusPDU) -> ModbusPDU | None:
        """Execute requests asynchronously.

        REMARK: this method is identical to sync_execute, apart from the lock and try/except.
                any changes in either method MUST be mirrored !!!
        """
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
        for call in (self.trace_recv_packet,
                     self.trace_recv_pdu,
                     self.trace_send_packet,
                     self.trace_send_pdu):
            if call:
                call(None)  # pylint: disable=not-callable

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        _ = (addr)
        if self.trace_recv_packet:
            data = self.trace_recv_packet(data)  # pylint: disable=not-callable
        try:
            used_len, pdu = self.framer.processIncomingFrame(data)
        except ModbusIOException as exc:
            if self.is_server:
                self.response_future.set_result((None, addr, exc))
            raise exc
        if pdu:
            if self.trace_recv_pdu:
                pdu = self.trace_recv_pdu(pdu)  # pylint: disable=not-callable
            result = (pdu, addr, None) if self.is_server else pdu
            self.response_future.set_result(result)
        return used_len

    def getNextTID(self) -> int:
        """Retrieve the next transaction identifier."""
        if self.next_tid >= 65000:
            self.next_tid = 1
        else:
            self.next_tid += 1
        return self.next_tid
