"""Fixtures for transport tests."""
import asyncio
import os
from contextlib import suppress
from unittest import mock

import pytest

from pymodbus.transport.transport import CommParams, CommType, NullModem, Transport


class DummyTransport(asyncio.BaseTransport):
    """Use in connection_made calls."""

    def transport_close(self):
        """Define dummy."""

    def transport_send(self):
        """Define dummy."""

    def close(self):
        """Define dummy."""

    def get_protocol(self):
        """Define dummy."""

    def is_closing(self):
        """Define dummy."""

    def set_protocol(self, _protocol):
        """Define dummy."""

    def abort(self):
        """Define dummy."""


@pytest.fixture(name="dummy_transport")
def prepare_dummy_transport():
    """Return transport object"""
    return DummyTransport()


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


@pytest.fixture(name="commparams")
def prepare_commparams(use_port, use_host, use_comm_type):
    """Prepare CommParamsClass object."""
    return CommParams(
        comm_name="test comm",
        comm_type=use_comm_type,
        reconnect_delay=1,
        reconnect_delay_max=3.5,
        timeout_connect=2,
        host=use_host,
        port=use_port,
        baudrate=9600,
        bytesize=8,
        parity="E",
        stopbits=2,
    )


@pytest.fixture(name="client")
async def prepare_transport(commparams):
    """Prepare transport object."""
    transport = Transport(commparams, False)
    with suppress(RuntimeError):
        transport.loop = asyncio.get_running_loop()
    transport.callback_connected = mock.Mock()
    transport.callback_disconnected = mock.Mock()
    transport.callback_data = mock.Mock(return_value=0)
    if commparams.comm_type == CommType.TLS:
        cwd = os.path.dirname(__file__) + "/../../examples/certificates/pymodbus."
        transport.comm_params.sslctx = commparams.generate_ssl(
            False, certfile=cwd + "crt", keyfile=cwd + "key"
        )
    if commparams.comm_type == CommType.SERIAL:
        transport.comm_params.host = f"socket://localhost:{transport.comm_params.port}"
    return transport


@pytest.fixture(name="server")
async def prepare_transport_server(commparams):
    """Prepare transport object."""
    transport = Transport(commparams, True)
    with suppress(RuntimeError):
        transport.loop = asyncio.get_running_loop()
    transport.callback_connected = mock.Mock()
    transport.callback_disconnected = mock.Mock()
    transport.callback_data = mock.Mock(return_value=0)
    if commparams.comm_type == CommType.TLS:
        cwd = os.path.dirname(__file__) + "/../../examples/certificates/pymodbus."
        transport.comm_params.sslctx = commparams.generate_ssl(
            True, certfile=cwd + "crt", keyfile=cwd + "key"
        )
    return transport


@pytest.fixture(name="nullmodem")
def prepare_nullmodem():
    """Prepare nullmodem object."""
    return NullModem(False, mock.Mock())


@pytest.fixture(name="nullmodem_server")
def prepare_nullmodem_server():
    """Prepare nullmodem object."""
    return NullModem(True, mock.Mock())
