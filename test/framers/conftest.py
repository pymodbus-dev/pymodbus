"""Configure pytest."""
from __future__ import annotations

from unittest import mock

import pytest

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer import AsyncFramer, FramerType
from pymodbus.transport import CommParams


@pytest.fixture(name="entry")
def prepare_entry():
    """Return framer_type."""
    return FramerType.ASCII

@pytest.fixture(name="is_server")
def prepare_is_server():
    """Return client/server."""
    return False

@mock.patch.multiple(AsyncFramer, __abstractmethods__=set())  # eliminate abstract methods (callbacks)
@pytest.fixture(name="dummy_async_framer")
async def prepare_test_framer(entry, is_server):
    """Return framer object."""
    framer = AsyncFramer(entry, CommParams(), is_server, [0, 1])  # type: ignore[abstract]
    framer.send = mock.Mock()  # type: ignore[method-assign]
    if entry == FramerType.RTU:
        func_table = (ServerDecoder if is_server else ClientDecoder)().lookup  # type: ignore[attr-defined]
        for key, ent in func_table.items():
            fix_len = getattr(ent, "_rtu_frame_size", 0)
            cnt_pos = getattr(ent, "_rtu_byte_count_pos", 0)
            framer.handle.set_fc_calc(key, fix_len, cnt_pos)
    return framer
