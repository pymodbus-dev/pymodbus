"""Test example server/client sync/async

This is a thorough test of the generic examples
(in principle examples that are used in other
examples, like run a server).
"""
import asyncio
import logging
from threading import Thread
from time import sleep

import pytest
import pytest_asyncio

from examples.client_async import run_async_client, setup_async_client
from examples.client_calls import run_sync_calls
from examples.client_sync import run_sync_client, setup_sync_client
from examples.client_test import run_async_calls as run_async_simple_calls
from examples.helper import get_commandline
from examples.server_async import run_async_server, setup_server
from examples.server_sync import run_sync_server
from pymodbus import pymodbus_apply_logging_config
from pymodbus.server import ServerAsyncStop, ServerStop


_logger = logging.getLogger()
_logger.setLevel("DEBUG")
pymodbus_apply_logging_config("DEBUG")
TEST_COMMS_FRAMER = [
    ("tcp", "socket", 5020),
    ("tcp", "rtu", 5020),
    ("tls", "tls", 5020),
    ("udp", "socket", 5020),
    ("udp", "rtu", 5020),
    ("serial", "rtu", "socket://127.0.0.1:5020"),
    # awaiting fix: ("serial", "ascii", "socket://127.0.0.1:5020"),
    # awaiting fix: ("serial", "binary", "socket://127.0.0.1:5020"),
]


@pytest_asyncio.fixture(name="mock_run_server")
async def _helper_server(
    test_comm,
    test_framer,
    test_port,
):
    """Run server."""
    cmdline = [
        "--comm",
        test_comm,
        "--port",
        str(test_port),
        "--framer",
        test_framer,
        "--baudrate",
        "9600",
        "--log",
        "debug",
    ]
    run_args = setup_server(cmdline=cmdline)
    task = asyncio.create_task(run_async_server(run_args))
    await asyncio.sleep(0.1)
    yield
    await ServerAsyncStop()
    task.cancel()
    await task


def test_get_commandline():
    """Test helper get_commandline()"""
    args = get_commandline(cmdline=["--log", "info"])
    assert args.log == "info"
    assert args.host == "127.0.0.1"


@pytest.mark.xdist_group(name="server_serialize")
@pytest.mark.parametrize(("test_comm", "test_framer", "test_port"), TEST_COMMS_FRAMER)
async def test_exp_async_server_client(
    test_comm,
    test_framer,
    test_port,
    mock_run_server,
):
    """Run async client and server."""
    assert not mock_run_server
    cmdline = [
        "--comm",
        test_comm,
        "--host",
        "127.0.0.1",
        "--framer",
        test_framer,
        "--port",
        str(test_port),
        "--baudrate",
        "9600",
        "--log",
        "debug",
    ]
    test_client = setup_async_client(cmdline=cmdline)
    await run_async_client(test_client, modbus_calls=run_async_simple_calls)


@pytest.mark.xdist_group(name="server_serialize")
@pytest.mark.parametrize(
    ("test_comm", "test_framer", "test_port"), [TEST_COMMS_FRAMER[0]]
)
def test_exp_sync_server_client(
    test_comm,
    test_framer,
    test_port,
):
    """Run sync client and server."""
    cmdline = [
        "--comm",
        test_comm,
        "--port",
        str(test_port),
        "--baudrate",
        "9600",
        "--log",
        "debug",
        "--framer",
        test_framer,
    ]
    run_args = setup_server(cmdline=cmdline)
    thread = Thread(target=run_sync_server, args=(run_args,))
    thread.daemon = True
    thread.start()
    sleep(1)
    test_client = setup_sync_client(cmdline=cmdline)
    run_sync_client(test_client, modbus_calls=run_sync_calls)
    ServerStop()
