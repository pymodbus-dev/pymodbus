"""ModbusProtocol network stub."""
from __future__ import annotations

from typing import Callable

from pymodbus.transport.transport import CommParams, ModbusProtocol


class ModbusProtocolStub(ModbusProtocol):
    """Protocol layer including transport."""

    def __init__(
        self,
        params: CommParams,
        is_server: bool,
        handler: Callable[[bytes], bytes] | None = None,
    ) -> None:
        """Initialize a stub instance."""
        self.stub_handle_data = handler if handler else self.dummy_handler
        super().__init__(params, is_server)


    async def start_run(self):
        """Call need functions to start server/client."""
        if  self.is_server:
            return await self.transport_listen()
        return await self.transport_connect()


    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        if (response := self.stub_handle_data(data)):
            self.transport_send(response)
        return len(data)

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        new_stub = ModbusProtocolStub(self.comm_params, False)
        new_stub.stub_handle_data = self.stub_handle_data
        return new_stub

    # ---------------- #
    # external methods #
    # ---------------- #
    def dummy_handler(self, data: bytes) -> bytes | None:
        """Handle received data."""
        return data
