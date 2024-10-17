"""Configure pytest."""
from __future__ import annotations

import pytest

from pymodbus.framer import FRAMER_NAME_TO_CLASS, FramerType
from pymodbus.pdu import DecodePDU


@pytest.fixture(name="entry")
def prepare_entry():
    """Return framer_type."""
    return FramerType.RTU

@pytest.fixture(name="is_server")
def prepare_is_server():
    """Return client/server."""
    return False

@pytest.fixture(name="test_framer")
async def prepare_test_framer(entry, is_server):
    """Return framer object."""
    return FRAMER_NAME_TO_CLASS[entry](DecodePDU(is_server))
