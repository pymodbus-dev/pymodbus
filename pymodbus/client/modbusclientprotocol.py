"""ModbusProtocol implementation for all clients."""
from __future__ import annotations

import asyncio
from collections.abc import Callable

from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.framer import FramerBase
from pymodbus.logging import Log
from pymodbus.pdu import ExceptionResponse, ModbusPDU
from pymodbus.transaction import ModbusTransactionManager
from pymodbus.transport import CommParams, ModbusProtocol


class ModbusClientProtocol(ModbusProtocol):
    """**ModbusClientProtocol**.

    :mod:`ModbusClientProtocol` is normally not referenced outside :mod:`pymodbus`.
    """

    def __init__(
        self,
        framer: FramerBase,
        params: CommParams,
        retries: int,
        on_connect_callback: Callable[[bool], None] | None = None,
    ) -> None:
        """Initialize a client instance."""
        ModbusProtocol.__init__(
            self,
            params,
            False,
        )
        self.retries = retries
        self.accept_no_response_limit = retries + 3
        self.on_connect_callback = on_connect_callback
        self.count_no_responses = 0

        # Common variables.
        self.framer = framer
        self.transaction = ModbusTransactionManager()
        self._lock = asyncio.Lock()

    def _old_handle_response(self, reply):
        """Handle the processed response and link to correct deferred."""
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                reply.request = handler
                if not handler.fut.done():
                    handler.fut.set_result(reply)
            else:
                Log.debug("Unrequested message: {}", reply, ":str")

    def old_build_response(self, request: ModbusPDU):
        """Return a deferred response for the current request.

        :meta private:
        """
        my_future: asyncio.Future = asyncio.Future()
        request.fut = my_future
        if not self.transport:
            if not my_future.done():
                my_future.set_exception(ConnectionException("Client is not connected"))
        else:
            self.transaction.addTransaction(request)
        return my_future


    async def local_execute(self, no_response_expected: bool, request) -> ModbusPDU | None:
        """Execute requests asynchronously.

        :meta private:
        """
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildFrame(request)

        count = 0
        async with self._lock:
            while count <= self.retries:
                req = self.old_build_response(request)
                self.send(packet)
                if no_response_expected:
                    resp = None
                    break
                try:
                    resp = await asyncio.wait_for(
                        req, timeout=self.comm_params.timeout_connect
                    )
                    break
                except asyncio.exceptions.TimeoutError:
                    count += 1
        if count > self.retries:
            if self.count_no_responses >= self.accept_no_response_limit:
                self.connection_lost(asyncio.TimeoutError("Server not responding"))
                raise ModbusIOException(
                    f"ERROR: No response received of the last {self.accept_no_response_limit} request, CLOSING CONNECTION."
                )
            self.count_no_responses += 1
            Log.error(f"No response received after {self.retries} retries, continue with next request")
            return ExceptionResponse(request.function_code)

        self.count_no_responses = 0
        return resp


    def callback_new_connection(self):
        """Call when listener receive new connection request."""

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""
        if self.on_connect_callback:
            self.loop.call_soon(self.on_connect_callback, True)

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""
        Log.debug("callback_disconnected called: {}", exc)
        if self.on_connect_callback:
            self.loop.call_soon(self.on_connect_callback, False)

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data.

        returns number of bytes consumed
        """
        used_len, pdu = self.framer.processIncomingFrame(data)
        if pdu:
            self._old_handle_response(pdu)
        return used_len

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return (
            f"{self.__class__.__name__} {self.comm_params.host}:{self.comm_params.port}"
        )
