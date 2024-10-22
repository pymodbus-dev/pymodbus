"""ModbusProtocol implementation for all clients."""
from __future__ import annotations

from collections.abc import Callable

from pymodbus.framer import (
    FRAMER_NAME_TO_CLASS,
    FramerBase,
    FramerType,
)
from pymodbus.logging import Log
from pymodbus.pdu import DecodePDU
from pymodbus.transaction import ModbusTransactionManager
from pymodbus.transport import CommParams, ModbusProtocol


class ModbusClientProtocol(ModbusProtocol):
    """**ModbusClientProtocol**.

    :mod:`ModbusClientProtocol` is normally not referenced outside :mod:`pymodbus`.
    """

    def __init__(
        self,
        framer: FramerType,
        params: CommParams,
        on_connect_callback: Callable[[bool], None] | None = None,
    ) -> None:
        """Initialize a client instance."""
        ModbusProtocol.__init__(
            self,
            params,
            False,
        )
        self.on_connect_callback = on_connect_callback

        # Common variables.
        self.framer: FramerBase = (FRAMER_NAME_TO_CLASS[framer])(DecodePDU(False))
        self.transaction = ModbusTransactionManager()

    def _handle_response(self, reply):
        """Handle the processed response and link to correct deferred."""
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                reply.request = handler
                if not handler.fut.done():
                    handler.fut.set_result(reply)
            else:
                Log.debug("Unrequested message: {}", reply, ":str")

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
            self._handle_response(pdu)
        return used_len

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return (
            f"{self.__class__.__name__} {self.comm_params.host}:{self.comm_params.port}"
        )
