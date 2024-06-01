"""Configure pytest."""
from __future__ import annotations

from unittest import mock

import pytest

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer import Framer, FramerType
from pymodbus.transport import CommParams, ModbusProtocol


class DummyFramer(Framer):
    """Implement use of ModbusProtocol."""

    def __init__(self,
            framer_type: FramerType,
            params: CommParams,
            is_server: bool,
            device_ids: list[int] | None,
        ):
        """Initialize a frame instance."""
        super().__init__(framer_type, params, is_server, device_ids)
        self.send = mock.Mock()
        self.framer_type = framer_type

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        return DummyFramer(self.framer_type, self.comm_params, self.is_server, self.device_ids)  # pragma: no cover

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""

    def callback_request_response(self, data: bytes, device_id: int, tid: int) -> None:
        """Handle received modbus request/response."""


@pytest.fixture(name="entry")
def prepare_entry():
    """Return framer_type."""
    return FramerType.RAW

@pytest.fixture(name="is_server")
def prepare_is_server():
    """Return client/server."""
    return False

@pytest.fixture(name="dummy_framer")
async def prepare_test_framer(entry, is_server):
    """Return framer object."""
    framer = DummyFramer(
        entry,
        CommParams(),
        is_server,
        [0, 1],
    )
    if entry == FramerType.RTU:
        func_table = (ServerDecoder if is_server else ClientDecoder)().lookup
        for key, ent in func_table.items():
            fix_len = ent._rtu_frame_size if hasattr(ent, "_rtu_frame_size") else 0  # pylint: disable=protected-access
            cnt_pos = ent. _rtu_byte_count_pos if hasattr(ent, "_rtu_byte_count_pos") else 0  # pylint: disable=protected-access
            framer.handle.set_fc_calc(key, fix_len, cnt_pos)
    return framer
