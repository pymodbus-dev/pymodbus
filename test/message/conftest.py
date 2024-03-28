"""Configure pytest."""
from __future__ import annotations

from unittest import mock

import pytest

from pymodbus.message import Message, MessageType
from pymodbus.transport import CommParams, ModbusProtocol


class DummyMessage(Message):
    """Implement use of ModbusProtocol."""

    def __init__(self,
            message_type: MessageType,
            params: CommParams,
            is_server: bool,
            device_ids: list[int] | None,
        ):
        """Initialize a message instance."""
        super().__init__(message_type, params, is_server, device_ids)
        self.send = mock.Mock()
        self.message_type = message_type

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        return DummyMessage(self.message_type, self.comm_params, self.is_server, self.device_ids)  # pragma: no cover

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""

    def callback_request_response(self, data: bytes, device_id: int, tid: int) -> None:
        """Handle received modbus request/response."""


@pytest.fixture(name="dummy_message")
async def prepare_dummy_message():
    """Return message object."""
    return DummyMessage
