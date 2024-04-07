"""ModbusProtocol implementation for all clients."""
from __future__ import annotations

from collections.abc import Callable
from typing import cast

from pymodbus.factory import ClientDecoder
from pymodbus.framer import FRAMER_NAME_TO_CLASS, FramerType, ModbusFramer
from pymodbus.logging import Log
from pymodbus.transaction import ModbusTransactionManager
from pymodbus.transport import CommParams, ModbusProtocol


class ModbusClientProtocol(ModbusProtocol):
    """**ModbusClientProtocol**.

    Fixed parameters:

    :param framer: Framer enum name
    :param params: Comm parameters for transport
    :param retries: Max number of retries per request.
    :param retry_on_empty: Retry on empty response.
    :param on_connect_callback: Will be called when connected/disconnected (bool parameter)

    :mod:`ModbusClientProtocol` is normally not referenced outside :mod:`pymodbus`.
    """

    def __init__(
        self,
        framer: FramerType,
        params: CommParams,
        retries: int,
        retry_on_empty: bool,
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
        self.framer = FRAMER_NAME_TO_CLASS.get(
            framer, cast(type[ModbusFramer], framer)
        )(ClientDecoder(), self)
        self.transaction = ModbusTransactionManager(
            self, retries=retries, retry_on_empty=retry_on_empty
        )

    def _handle_response(self, reply, **_kwargs):
        """Handle the processed response and link to correct deferred."""
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                if not handler.done():
                    handler.set_result(reply)
            else:
                Log.debug("Unrequested message: {}", reply, ":str")

    def callback_new_connection(self):
        """Call when listener receive new connection request."""

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""
        if self.on_connect_callback:
            self.loop.call_soon(self.on_connect_callback, True)
        self.framer.resetFrame()

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""
        Log.debug("callback_disconnected called: {}", exc)
        if self.on_connect_callback:
            self.loop.call_soon(self.on_connect_callback, False)

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data.

        returns number of bytes consumed
        """
        self.framer.processIncomingPacket(data, self._handle_response, slave=0)
        return len(data)

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return (
            f"{self.__class__.__name__} {self.comm_params.host}:{self.comm_params.port}"
        )
