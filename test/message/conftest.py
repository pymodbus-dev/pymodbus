"""Configure pytest."""
from __future__ import annotations

import pytest

from pymodbus.logging import Log
from pymodbus.message import Message
from pymodbus.transport import ModbusProtocol


class DummyMessage(Message):
    """Implement use of ModbusProtocol."""

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        return DummyMessage(self.message_type, self.comm_params, self.is_server, self.device_ids)

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""
        Log.debug("callback_disconnected called: {}", exc)

    def callback_request_response(self, data: bytes, tid: int) -> None:
        """Handle received modbus request/response."""


@pytest.fixture(name="dummy_message")
async def prepare_dummy_message():
    """Return message object."""
    return DummyMessage
