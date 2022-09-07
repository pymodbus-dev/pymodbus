#!/usr/bin/env python3
"""Test client async."""
import asyncio
from dataclasses import dataclass
from threading import Thread
from time import sleep
import logging

from unittest.mock import patch, MagicMock
import pytest
import pytest_asyncio

from examples.client_async import run_async_client, setup_async_client
from examples.client_async_basic_calls import run_async_basic_calls
from examples.client_async_extended_calls import run_async_ext_calls
from examples.server_async import run_async_server
from examples.server_sync import run_sync_server

from pymodbus.server import ServerStop, ServerAsyncStop
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


_logger = logging.getLogger()
_logger.setLevel("DEBUG")

TEST_COMMS_FRAMER = [
    ("tcp", ModbusSocketFramer, 5020),
    ("tcp", ModbusRtuFramer, 5021),
    ("tls", ModbusTlsFramer, 5030),
    ("udp", ModbusSocketFramer, 5040),
    ("udp", ModbusRtuFramer, 5041),
    ("serial", ModbusRtuFramer, "dummy"),
    ("serial", ModbusAsciiFramer, "dummy"),
    ("serial", ModbusBinaryFramer, "dummy"),
]


@dataclass
class Commandline:
    """Simulate commandline parameters."""

    comm = None
    framer = None
    port = None
    store = "sequential"
    slaves = None


@pytest_asyncio.fixture(name="mock_libs")
def _helper_libs():
    """Patch ssl and pyserial-async libs."""
    with patch('pymodbus.server.async_io.create_serial_connection') as mock_serial:
        mock_serial.return_value = (MagicMock(), MagicMock())
        yield True


@pytest_asyncio.fixture(name="mock_run_server")
async def _helper_server(  # pylint: disable=unused-argument
    mock_libs,
    test_comm,
    test_framer,
    test_port,
):
    """Run server."""
    args = Commandline
    args.comm = test_comm
    args.framer = test_framer
    args.port = test_port
    asyncio.create_task(run_async_server(args))
    await asyncio.sleep(0.1)
    yield True
    await ServerAsyncStop()
    tasks = asyncio.all_tasks()
    owntask = asyncio.current_task()
    for i in [i for i in tasks if not (i.done() or i.cancelled() or i == owntask)]:
        i.cancel()


async def run_client(
    test_comm,
    test_type,
    args=Commandline
):
    """Help run async client."""

    args.comm = test_comm
    test_client = setup_async_client(args=args)
    if not test_type:
        await run_async_client(test_client)
    else:
        await run_async_client(test_client, modbus_calls=test_type)
    await asyncio.sleep(0.1)


@pytest.mark.parametrize("test_comm, test_framer, test_port", TEST_COMMS_FRAMER)
async def test_exp_async_simple(  # pylint: disable=unused-argument
    test_comm,
    test_framer,
    test_port,
    mock_run_server,
):
    """Run async client and server."""


@pytest.mark.parametrize("test_comm, test_framer, test_port", TEST_COMMS_FRAMER)
def test_exp_sync_simple(  # pylint: disable=unused-argument
    mock_libs,
    test_comm,
    test_framer,
    test_port,
):
    """Run sync client and server."""
    args = Commandline
    args.comm = test_comm
    args.port = test_port
    thread = Thread(target=run_sync_server, args=(args,))
    thread.daemon = True
    thread.start()
    sleep(0.1)
    ServerStop()


@pytest.mark.parametrize("test_comm, test_framer, test_port", TEST_COMMS_FRAMER)
@pytest.mark.parametrize(
    "test_type",
    [
        None,
        run_async_basic_calls,
        run_async_ext_calls,
    ],
)
async def test_exp_async_framer(  # pylint: disable=unused-argument
    test_comm,
    test_framer,
    test_port,
    mock_run_server,
    test_type
):
    """Test client-server async with different framers and calls."""
    if test_type == run_async_ext_calls and test_framer == ModbusRtuFramer:  # pylint: disable=comparison-with-callable
        return
    if test_comm == "tls" and test_type:
        # mocking cert operations prevent connect.
        return
    if test_comm == "serial":
        # mocking serial needs to pass data between send/receive
        return

    args = Commandline
    args.framer = test_framer
    args.comm = test_comm
    args.port = test_port
    await run_client(test_comm, test_type, args=args)
