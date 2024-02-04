"""ModbusProtocol network stub."""
from __future__ import annotations

from pymodbus.transport.transport import ModbusProtocol


class ModbusProtocolStub(ModbusProtocol):
    """Protocol layer including transport."""

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
        return ModbusProtocolStub(self.comm_params, False)

    # ---------------- #
    # external methods #
    # ---------------- #
    def stub_handle_data(self, data: bytes) -> bytes | None:
        """Handle received data."""
        return data
