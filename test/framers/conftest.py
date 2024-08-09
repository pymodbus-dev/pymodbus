"""Configure pytest."""
from __future__ import annotations

from unittest import mock

import pytest

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer import Framer, FramerType
from pymodbus.transport import CommParams


@pytest.fixture(name="entry")
def prepare_entry():
    """Return framer_type."""
    return FramerType.RAW

@pytest.fixture(name="is_server")
def prepare_is_server():
    """Return client/server."""
    return False

@mock.patch.multiple(Framer, __abstractmethods__=set())  # eliminate abstract methods (callbacks)
@pytest.fixture(name="dummy_framer")
async def prepare_test_framer(entry, is_server):
    """Return framer object."""
    framer = Framer(entry, CommParams(), is_server, [0, 1])  # type: ignore[abstract]
    framer.send = mock.Mock()  # type: ignore[method-assign]
    if entry == FramerType.RTU:
        func_table = (ServerDecoder if is_server else ClientDecoder)().lookup
        for key, ent in func_table.items():
            fix_len = ent._rtu_frame_size if hasattr(ent, "_rtu_frame_size") else 0  # pylint: disable=protected-access
            cnt_pos = ent. _rtu_byte_count_pos if hasattr(ent, "_rtu_byte_count_pos") else 0  # pylint: disable=protected-access
            framer.handle.set_fc_calc(key, fix_len, cnt_pos)
    return framer
