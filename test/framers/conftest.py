"""Configure pytest."""
from __future__ import annotations

import pytest

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer import FRAMER_NAME_TO_CLASS, FramerType


@pytest.fixture(name="entry")
def prepare_entry():
    """Return framer_type."""
    return FramerType.RTU

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
