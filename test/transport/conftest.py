"""Configure pytest."""
from __future__ import annotations

import os
import sys
from unittest import mock

import pytest

from pymodbus.logging import Log
from pymodbus.transport import CommParams, CommType, ModbusProtocol


sys.path.extend(["examples", "../examples", "../../examples"])


class DummyProtocol(ModbusProtocol):
    """Use in connection_made calls."""

    def __init__(self, params=CommParams(), is_server=False):
        """Initialize."""
        #  self.connection_made = mock.Mock()
        #  self.connection_lost = mock.Mock()
        super().__init__(params, is_server)

    def callback_new_connection(self) -> ModbusProtocol:
        """Call when listener receive new connection request."""
        return DummyProtocol(params=self.comm_params, is_server=False)

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data."""
        Log.debug("callback_data called: {} addr={}", data, ":hex", addr)
        return 0


@pytest.fixture(name="dummy_protocol")
async def prepare_dummy_protocol():
    """Return transport object."""
    return DummyProtocol


@pytest.fixture(name="client")
async def prepare_protocol(use_clc):
    """Prepare transport object."""
    if use_clc.comm_type == CommType.TLS:
        cwd = os.path.dirname(__file__) + "/../../examples/certificates/pymodbus."
        use_clc.sslctx = use_clc.generate_ssl(
            False, certfile=cwd + "crt", keyfile=cwd + "key"
        )
    transport = DummyProtocol(params=use_clc, is_server=False)
    transport.callback_connected = mock.Mock()
    transport.callback_disconnected = mock.Mock()
    transport.callback_data = mock.Mock(return_value=0)
    if use_clc.comm_type == CommType.SERIAL:
        transport.comm_params.host = f"socket://localhost:{transport.comm_params.port}"
    return transport


@pytest.fixture(name="server")
async def prepare_transport_server(use_cls):
    """Prepare transport object."""
    if use_cls.comm_type == CommType.TLS:
        cwd = os.path.dirname(__file__) + "/../../examples/certificates/pymodbus."
        use_cls.sslctx = use_cls.generate_ssl(
            True, certfile=cwd + "crt", keyfile=cwd + "key"
        )
    transport = DummyProtocol(params=use_cls, is_server=True)
    transport.callback_connected = mock.Mock()
    transport.callback_disconnected = mock.Mock()
    transport.callback_data = mock.Mock(return_value=0)
    return transport
