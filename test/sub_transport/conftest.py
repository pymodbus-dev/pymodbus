"""Fixtures for transport tests."""
import asyncio
from unittest import mock

import pytest

from pymodbus.transport import (
    CommParams,
    ModbusProtocol,
)


class DummyProtocol(ModbusProtocol):
    """Use in connection_made calls."""

    def __init__(self, is_server=False):  # pylint: disable=super-init-not-called
        """Initialize."""
        self.comm_params = CommParams()
        self.transport = None
        self.is_server = is_server
        self.is_closing = False
        self.data = b""
        self.connection_made = mock.Mock()
        self.connection_lost = mock.Mock()
        self.reconnect_task: asyncio.Task = None

    def handle_new_connection(self):
        """Handle incoming connect."""
        if not self.is_server:
            # Clients reuse the same object.
            return self
        return DummyProtocol()

    def close(self):
        """Simulate close."""
        self.is_closing = True

    def data_received(self, data):
        """Call when some data is received."""
        self.data += data


@pytest.fixture(name="dummy_protocol")
def prepare_dummy_protocol():
    """Return transport object."""
    return DummyProtocol
