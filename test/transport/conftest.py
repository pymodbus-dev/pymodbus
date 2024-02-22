"""Configure pytest."""
import asyncio
import os
import sys
from unittest import mock

import pytest

from pymodbus.transport import CommParams, CommType, ModbusProtocol


sys.path.extend(["examples", "../examples", "../../examples"])


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
async def prepare_dummy_protocol():
    """Return transport object."""
    return DummyProtocol


@pytest.fixture(name="client")
async def prepare_protocol(use_clc):
    """Prepare transport object."""
    transport = ModbusProtocol(use_clc, False)
    transport.callback_connected = mock.Mock()
    transport.callback_disconnected = mock.Mock()
    transport.callback_data = mock.Mock(return_value=0)
    if use_clc.comm_type == CommType.TLS:
        cwd = os.path.dirname(__file__) + "/../../examples/certificates/pymodbus."
        transport.comm_params.sslctx = use_clc.generate_ssl(
            False, certfile=cwd + "crt", keyfile=cwd + "key"
        )
    if use_clc.comm_type == CommType.SERIAL:
        transport.comm_params.host = f"socket://localhost:{transport.comm_params.port}"
    return transport


@pytest.fixture(name="server")
async def prepare_transport_server(use_cls):
    """Prepare transport object."""
    transport = ModbusProtocol(use_cls, True)
    transport.callback_connected = mock.Mock()
    transport.callback_disconnected = mock.Mock()
    transport.callback_data = mock.Mock(return_value=0)
    if use_cls.comm_type == CommType.TLS:
        cwd = os.path.dirname(__file__) + "/../../examples/certificates/pymodbus."
        transport.comm_params.sslctx = use_cls.generate_ssl(
            True, certfile=cwd + "crt", keyfile=cwd + "key"
        )
    return transport
