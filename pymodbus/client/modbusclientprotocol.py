"""ModbusProtocol implementation for all clients."""
from __future__ import annotations

from collections.abc import Callable

from pymodbus.framer import FramerBase
from pymodbus.logging import Log
from pymodbus.transaction import TransactionManager
from pymodbus.transport import CommParams


class ModbusClientProtocol(TransactionManager):
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
        super().__init__(params, framer, retries, False)
        self.on_connect_callback = on_connect_callback

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""
        super().callback_connected()
        if self.on_connect_callback:
            self.loop.call_soon(self.on_connect_callback, True)

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""
        Log.debug("callback_disconnected called: {}", exc)
        super().callback_disconnected(exc)
        if self.on_connect_callback:
            self.loop.call_soon(self.on_connect_callback, False)

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return (
            f"{self.__class__.__name__} {self.comm_params.host}:{self.comm_params.port}"
        )
