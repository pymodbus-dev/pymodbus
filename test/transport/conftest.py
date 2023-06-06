"""Test transport."""
import asyncio
import os
from contextlib import suppress
from dataclasses import dataclass
from unittest import mock

import pytest
import pytest_asyncio

from pymodbus.transport.transport import Transport


@dataclass
class BaseParams(Transport.CommParamsClass):
    """Base parameters for all transport testing."""

    comm_name = "test comm"
    reconnect_delay = 1000
    reconnect_delay_max = 3500
    timeout_connect = 2000
    host = "test host"
    port = 502
    server_hostname = "server test host"
    baudrate = 9600
    bytesize = 8
    parity = "e"
    stopbits = 2
    cwd = os.path.dirname(__file__) + "/../../examples/certificates/pymodbus."


@pytest.fixture(name="params")
def prepare_baseparams():
    """Prepare BaseParams class."""
    return BaseParams


class DummySocket:  # pylint: disable=too-few-public-methods
    """Socket simulator for test."""

    def __init__(self):
        """Initialize."""
        self.close = mock.Mock()
        self.abort = mock.Mock()


@pytest.fixture(name="dummy_socket")
def prepare_dummysocket():
    """Prepare dummy_socket class."""
    return DummySocket


@pytest.fixture(name="commparams")
def prepare_testparams():
    """Prepare CommParamsClass object."""
    return Transport.CommParamsClass(
        done=True,
        comm_name=BaseParams.comm_name,
        reconnect_delay=BaseParams.reconnect_delay / 1000,
        reconnect_delay_max=BaseParams.reconnect_delay_max / 1000,
        timeout_connect=BaseParams.timeout_connect / 1000,
    )


@pytest.fixture(name="transport")
async def prepare_transport():
    """Prepare transport object."""
    transport = Transport(
        BaseParams.comm_name,
        BaseParams.reconnect_delay,
        BaseParams.reconnect_delay_max,
        BaseParams.timeout_connect,
        mock.Mock(name="cb_connection_made"),
        mock.Mock(name="cb_connection_lost"),
        mock.Mock(name="cb_handle_data", return_value=0),
    )
    with suppress(RuntimeError):
        transport.loop = asyncio.get_running_loop()
    return transport


@pytest_asyncio.fixture(name="transport_server")
async def prepare_transport_server():
    """Prepare transport object."""
    transport = Transport(
        BaseParams.comm_name,
        BaseParams.reconnect_delay,
        BaseParams.reconnect_delay_max,
        BaseParams.timeout_connect,
        mock.Mock(name="cb_connection_made"),
        mock.Mock(name="cb_connection_lost"),
        mock.Mock(name="cb_handle_data", return_value=0),
    )
    with suppress(RuntimeError):
        transport.loop = asyncio.get_running_loop()
    return transport
