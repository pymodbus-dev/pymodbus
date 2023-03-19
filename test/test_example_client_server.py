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
from examples.client_calls import run_async_calls, run_sync_calls
from examples.client_sync import run_sync_client, setup_sync_client
from examples.helper import get_commandline
from examples.server_async import run_async_server, setup_server
from examples.server_sync import run_sync_server
from pymodbus import pymodbus_apply_logging_config
from pymodbus.server import ServerAsyncStop, ServerStop
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


_logger = logging.getLogger()
_logger.setLevel("DEBUG")
pymodbus_apply_logging_config("DEBUG")
TEST_COMMS_FRAMER = [
    ("tcp", "socket", 5020),
    ("tcp", "rtu", 5021),
    ("tls", "tls", 5020),
    ("udp", "socket", 5020),
    ("udp", "rtu", 5021),
    ("serial", "rtu", 5020),
    ("serial", "ascii", 5021),
    ("serial", "binary", 5022),
]
TEST_CONVERT_FRAMER = {
    "socket": ModbusSocketFramer,
    "rtu": ModbusRtuFramer,
    "tls": ModbusTlsFramer,
    "ascii": ModbusAsciiFramer,
    "binary": ModbusBinaryFramer,
}


@pytest_asyncio.fixture(name="mock_run_server")
async def _helper_server(
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
):
    """Run server."""
    if pytest.IS_WINDOWS and test_comm == "serial":
        yield
        return
    port = test_port + test_port_offset
    if test_comm == "serial":
        port = f"socket://127.0.0.1:{port}"
    cmdline = [
        "--comm",
        test_comm,
        "--port",
        str(port),
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


async def run_client(test_comm, test_type, port=None, cmdline=None):
    """Help run async client."""
    if not cmdline:
        cmdline = [
            "--comm",
            test_comm,
            "--host",
            "127.0.0.1",
            "--baudrate",
            "9600",
            "--log",
            "debug",
        ]
    if test_comm == "serial":
        port = f"socket://127.0.0.1:{port}"

    cmdline.extend(
        [
            "--port",
            str(port),
        ]
    )

    test_client = setup_async_client(cmdline=cmdline)
    if not test_type:
        await run_async_client(test_client)
    else:
        await run_async_client(test_client, modbus_calls=test_type)
    await asyncio.sleep(0.1)


def test_get_commandline():
    """Test helper get_commandline()"""
    args = get_commandline(cmdline=["--log", "info"])
    assert args.log == "info"
    assert args.host == "127.0.0.1"


@pytest.mark.xdist_group(name="server_serialize")
@pytest.mark.parametrize("test_port_offset", [10])
@pytest.mark.parametrize("test_comm, test_framer, test_port", TEST_COMMS_FRAMER)
async def test_exp_async_server_client(
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
    mock_run_server,
):
    """Run async client and server."""
    # JAN WAITING
    if pytest.IS_WINDOWS and test_comm == "serial":
        return
    if test_comm in {"tcp", "tls"}:
        return
    assert not mock_run_server

    port = test_port + test_port_offset
    cmdline = [
        "--comm",
        test_comm,
        "--host",
        "127.0.0.1",
        "--framer",
        test_framer,
        "--baudrate",
        "9600",
        "--log",
        "debug",
    ]

    await run_client(test_comm, None, port=port, cmdline=cmdline)


@pytest.mark.xdist_group(name="server_serialize")
@pytest.mark.parametrize("test_port_offset", [20])
@pytest.mark.parametrize("test_comm, test_framer, test_port", [TEST_COMMS_FRAMER[0]])
def test_exp_sync_server_client(
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
):
    """Run sync client and server."""
    port = test_port + test_port_offset
    cmdline = [
        "--comm",
        test_comm,
        "--port",
        str(port),
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


# JAN
@pytest.mark.xdist_group(name="server_serialize")
@pytest.mark.parametrize("test_port_offset", [30])
@pytest.mark.parametrize("test_comm, test_framer, test_port", TEST_COMMS_FRAMER)
async def xtest_exp_framers_calls(
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
    mock_run_server,
):
    """Test client-server async with different framers and calls."""
    assert not mock_run_server
    if test_comm == "serial" and test_framer in (ModbusAsciiFramer, ModbusBinaryFramer):
        return
    if pytest.IS_WINDOWS and test_comm == "serial":
        return
    port = test_port + test_port_offset
    cmdline = [
        "--comm",
        test_comm,
        "--host",
        "127.0.0.1",
        "--framer",
        test_framer,
        "--baudrate",
        "9600",
        "--log",
        "debug",
    ]
    await run_client(test_comm, run_async_calls, port=port, cmdline=cmdline)
