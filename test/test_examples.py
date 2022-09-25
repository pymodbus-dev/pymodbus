#!/usr/bin/env python3
"""Test client async."""
import asyncio
from dataclasses import dataclass
from threading import Thread
from time import sleep
import logging

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
    ("tcp", ModbusSocketFramer, 5021),
    ("tcp", ModbusRtuFramer, 5022),
    ("tls", ModbusTlsFramer, 5023),
    ("udp", ModbusSocketFramer, 5024),
    ("udp", ModbusRtuFramer, 5025),
    ("serial", ModbusRtuFramer, "socket://127.0.0.1:5026"),
    ("serial", ModbusAsciiFramer, "socket://127.0.0.1:5027"),
    ("serial", ModbusBinaryFramer, "socket://127.0.0.1:5028"),
]


@dataclass
class Commandline:
    """Simulate commandline parameters."""

    comm = None
    framer = None
    port = None
    store = "sequential"
    slaves = None


@pytest_asyncio.fixture(name="mock_run_server")
async def _helper_server(
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
):
    """Run server."""
    args = Commandline
    args.comm = test_comm
    args.framer = test_framer
    args.port = test_port
    if isinstance(test_port, int):
        args.port += test_port_offset
    asyncio.create_task(run_async_server(args))
    await asyncio.sleep(0.1)
    yield
    await ServerAsyncStop()


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


@pytest.mark.parametrize("test_port_offset", [10])
@pytest.mark.parametrize("test_comm, test_framer, test_port", TEST_COMMS_FRAMER)
async def test_exp_async_simple(  # pylint: disable=unused-argument
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
    mock_run_server,
):
    """Run async client and server."""


@pytest.mark.parametrize("test_port_offset", [20])
@pytest.mark.parametrize("test_comm, test_framer, test_port", TEST_COMMS_FRAMER)
def test_exp_sync_simple(
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
):
    """Run sync client and server."""
    if test_comm == "serial":
        # missing mock of port
        return
    args = Commandline
    args.comm = test_comm
    args.port = test_port + test_port_offset
    args.framer = test_framer
    thread = Thread(target=run_sync_server, args=(args,))
    thread.daemon = True
    thread.start()
    sleep(1)
    ServerStop()


@pytest.mark.parametrize("test_port_offset", [30])
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
    test_port_offset,
    test_port,
    mock_run_server,
    test_type
):
    """Test client-server async with different framers and calls."""
    if test_type == run_async_ext_calls and test_framer == ModbusRtuFramer:  # pylint: disable=comparison-with-callable
        return
    if test_comm == "serial":
        return

    args = Commandline
    args.framer = test_framer
    args.comm = test_comm
    args.port = test_port
    if isinstance(test_port, int):
        args.port += test_port_offset
    await run_client(test_comm, test_type, args=args)
