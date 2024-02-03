"""ModbusProtocol network stub."""
from __future__ import annotations

from pymodbus.transport.transport import CommParams, ModbusProtocol


class ModbusProtocolStub(ModbusProtocol):
    """Protocol layer including transport."""

    def __init__(
        self,
        params: CommParams,
        is_server: bool,
    ) -> None:
        """Initialize Network stub."""
        super().__init__(params, is_server)

    async def start_run(self):
        """Call need functions to start server/client."""
        if  self.is_server:
            return await self.transport_listen()
        else:
            return await self.transport_connect()

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        response = self.stub_handle_data(data)
        if response:
            self.transport_send(response)
        return len(data)

    # ---------------- #
    # external methods #
    # ---------------- #
    def stub_handle_data(self, data: bytes) -> bytes | None:
        """Handle received data."""
        return None
