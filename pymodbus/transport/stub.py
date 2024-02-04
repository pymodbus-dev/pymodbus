"""ModbusProtocol network stub."""
from __future__ import annotations

from pymodbus.transport.transport import ModbusProtocol


class ModbusProtocolStub(ModbusProtocol):
    """Protocol layer including transport."""

    async def start_run(self):
        """Call need functions to start server/client."""
        if  self.is_server:
            await self.transport_listen()
        else:
            await self.transport_connect()
        self.transport = self

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        if (response := self.stub_handle_data(data)):
            self.transport_send(response)
        return len(data)

    # ---------------- #
    # external methods #
    # ---------------- #
    def stub_handle_data(self, data: bytes) -> bytes | None:
        """Handle received data."""
        if len(data) > 5:
            return data
        return None
