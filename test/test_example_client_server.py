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
from examples.helper import Commandline, get_commandline
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
    ("tcp", ModbusSocketFramer, 5020),
    ("tcp", ModbusRtuFramer, 5021),
    ("tls", ModbusTlsFramer, 5020),
    ("udp", ModbusSocketFramer, 5020),
    ("udp", ModbusRtuFramer, 5021),
    ("serial", ModbusRtuFramer, 5020),
    ("serial", ModbusAsciiFramer, 5021),
    ("serial", ModbusBinaryFramer, 5022),
]


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
    args = Commandline.copy()
    args.comm = test_comm
    args.framer = test_framer
    args.port = test_port + test_port_offset
    if test_comm == "serial":
        args.port = f"socket://127.0.0.1:{args.port}"
    run_args = setup_server(args)
    task = asyncio.create_task(run_async_server(run_args))
    await asyncio.sleep(0.1)
    yield
    await ServerAsyncStop()
    task.cancel()
    await task


async def run_client(test_comm, test_type, args=Commandline.copy()):
    """Help run async client."""

    args.comm = test_comm
    if test_comm == "serial":
        args.port = f"socket://127.0.0.1:{args.port}"
    test_client = setup_async_client(args=args)
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
    args = Commandline.copy()
    args.framer = test_framer
    args.comm = test_comm
    args.port = test_port + test_port_offset
    await run_client(test_comm, None, args=args)


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
    args = Commandline.copy()
    args.comm = test_comm
    args.port = test_port + test_port_offset
    args.framer = test_framer
    run_args = setup_server(args)
    thread = Thread(target=run_sync_server, args=(run_args,))
    thread.daemon = True
    thread.start()
    sleep(1)
    test_client = setup_sync_client(args=args)
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
    args = Commandline.copy()
    args.framer = test_framer
    args.comm = test_comm
    args.port = test_port + test_port_offset
    await run_client(test_comm, run_async_calls, args=args)
