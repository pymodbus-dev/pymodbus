"""Fixtures for transport tests."""
import asyncio
import os
from unittest import mock

import pytest

from pymodbus.transport import (
    NULLMODEM_HOST,
    CommParams,
    CommType,
    ModbusProtocol,
    NullModem,
)


class DummyProtocol(ModbusProtocol):
    """Use in connection_made calls."""

    def __init__(self, is_server=False):  # pylint: disable=super-init-not-called
        """Initialize"""
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
    """Return transport object"""
    return DummyProtocol


@pytest.fixture(name="cwd_certificate")
def prepare_cwd_certificate():
    """Prepare path to certificate."""
    return os.path.dirname(__file__) + "/../../examples/certificates/pymodbus."


@pytest.fixture(name="use_comm_type")
def prepare_dummy_use_comm_type():
    """Return default comm_type"""
    return CommType.TCP


@pytest.fixture(name="use_host")
def prepare_dummy_use_host():
    """Return default host"""
    return "localhost"


@pytest.fixture(name="use_cls")
def prepare_commparams_server(use_port, use_host, use_comm_type):
    """Prepare CommParamsClass object."""
    if use_host == NULLMODEM_HOST and use_comm_type == CommType.SERIAL:
        use_host = f"{NULLMODEM_HOST}:{use_port}"
    return CommParams(
        comm_name="test comm",
        comm_type=use_comm_type,
        reconnect_delay=0,
        reconnect_delay_max=0,
        timeout_connect=0,
        source_address=(use_host, use_port),
        baudrate=9600,
        bytesize=8,
        parity="E",
        stopbits=2,
    )


@pytest.fixture(name="use_clc")
def prepare_commparams_client(use_port, use_host, use_comm_type):
    """Prepare CommParamsClass object."""
    if use_host == NULLMODEM_HOST and use_comm_type == CommType.SERIAL:
        use_host = f"{NULLMODEM_HOST}:{use_port}"
    timeout = 10 if not pytest.IS_WINDOWS else 5
    return CommParams(
        comm_name="test comm",
        comm_type=use_comm_type,
        reconnect_delay=1,
        reconnect_delay_max=3.5,
        timeout_connect=timeout,
        host=use_host,
        port=use_port,
        baudrate=9600,
        bytesize=8,
        parity="E",
        stopbits=2,
    )


@pytest.fixture(name="client")
def prepare_protocol(use_clc):
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
def prepare_transport_server(use_cls):
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


@pytest.fixture(name="nullmodem")
def prepare_nullmodem():
    """Prepare nullmodem object."""
    return NullModem(mock.Mock())


@pytest.fixture(name="nullmodem_server")
def prepare_nullmodem_server():
    """Prepare nullmodem object."""
    return NullModem(mock.Mock())
