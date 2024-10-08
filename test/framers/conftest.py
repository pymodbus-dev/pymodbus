"""Configure pytest."""
from __future__ import annotations

from unittest import mock

import pytest

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer import FRAMER_NAME_TO_CLASS, AsyncFramer, FramerType
from pymodbus.transport import CommParams


@pytest.fixture(name="entry")
def prepare_entry():
    """Return framer_type."""
    return FramerType.ASCII

@pytest.fixture(name="is_server")
def prepare_is_server():
    """Return client/server."""
    return False

@pytest.fixture(name="dev_ids")
def prepare_dev_ids():
    """Return list of device ids."""
    return [0, 17]

@pytest.fixture(name="test_framer")
async def prepare_test_framer(entry, is_server, dev_ids):
    """Return framer object."""
    return FRAMER_NAME_TO_CLASS[entry](
        (ServerDecoder if is_server else ClientDecoder)(),
        dev_ids,
    )





@mock.patch.multiple(AsyncFramer, __abstractmethods__=set())  # eliminate abstract methods (callbacks)
@pytest.fixture(name="dummy_async_framer")
async def prepare_test_async_framer(entry, is_server):
    """Return framer object."""
    decoder = (ServerDecoder if is_server else ClientDecoder)()
    framer = AsyncFramer(entry, CommParams(), is_server, decoder, [0, 1])  # type: ignore[abstract]
    framer.send = mock.Mock()  # type: ignore[method-assign]
    #if entry == FramerType.RTU:
        #func_table = decoder.lookup  # type: ignore[attr-defined]
        #for key, ent in func_table.items():
        #    fix_len = getattr(ent, "_rtu_frame_size", 0)
        #    cnt_pos = getattr(ent, "_rtu_byte_count_pos", 0)
        #    framer.handle.set_fc_calc(key, fix_len, cnt_pos)
    return framer
