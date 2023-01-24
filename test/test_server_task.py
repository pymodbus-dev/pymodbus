"""Test client/server stop/start."""
import asyncio
import logging
import os
from time import sleep

import pytest

from pymodbus import client, pymodbus_apply_logging_config, server
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.transaction import (
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


_logger = logging.getLogger()
pymodbus_apply_logging_config(logging.DEBUG)
_logger.setLevel(logging.DEBUG)

TEST_TYPES = ["tcp", "udp", "serial", "tls"]


def helper_config(request, def_type):
    """Do setup of single test-"""
    pymodbus_apply_logging_config()
    _logger.setLevel("DEBUG")
    datablock = ModbusSequentialDataBlock(0x00, [17] * 100)
    context = ModbusServerContext(
        slaves=ModbusSlaveContext(
            di=datablock, co=datablock, hr=datablock, ir=datablock, unit=1
        ),
        single=True,
    )
    cwd = os.getcwd().split("/")[-1]
    path = "../examples" if cwd == "test" else "examples"
    cfg = {
        "serial": {
            "srv_args": {
                "context": context,
                "framer": ModbusRtuFramer,
                "port": "socket://127.0.0.1:5020",
            },
            "cli_args": {
                "framer": ModbusRtuFramer,
                "port": "socket://127.0.0.1:5020",
                "timeout": 0.2,
            },
            "async": {
                "srv": server.StartAsyncSerialServer,
                "cli": client.AsyncModbusSerialClient,
            },
            "sync": {
                "srv": "server.StartSerialServer",
                "cli": client.ModbusSerialClient,
            },
        },
        "tcp": {
            "srv_args": {
                "context": context,
                "framer": ModbusSocketFramer,
                "address": ("127.0.0.1", 5020),
                "allow_reuse_address": True,
            },
            "cli_args": {
                "framer": ModbusSocketFramer,
                "host": "127.0.0.1",
                "port": 5020,
                "timeout": 0.2,
            },
            "async": {
                "srv": server.StartAsyncTcpServer,
                "cli": client.AsyncModbusTcpClient,
            },
            "sync": {
                "srv": "server.StartTcpServer",
                "cli": client.ModbusTcpClient,
            },
        },
        "tls": {
            "srv_args": {
                "context": context,
                "framer": ModbusTlsFramer,
                "address": ("127.0.0.1", 5020),
                "allow_reuse_address": True,
                "certfile": f"{path}/certificates/pymodbus.crt",
                "keyfile": f"{path}/certificates/pymodbus.key",
            },
            "cli_args": {
                "framer": ModbusTlsFramer,
                "host": "127.0.0.1",
                "port": 5020,
                "certfile": f"{path}/certificates/pymodbus.crt",
                "keyfile": f"{path}/certificates/pymodbus.key",
                "server_hostname": "localhost",
                "timeout": 0.2,
            },
            "async": {
                "srv": server.StartAsyncTlsServer,
                "cli": client.AsyncModbusTlsClient,
            },
            "sync": {
                "srv": "server.StartTlsServer",
                "cli": client.ModbusTlsClient,
            },
        },
        "udp": {
            "srv_args": {
                "context": context,
                "framer": ModbusSocketFramer,
                "address": ("127.0.0.1", 5020),
            },
            "cli_args": {
                "framer": ModbusSocketFramer,
                "host": "127.0.0.1",
                "port": 5020,
                "timeout": 0.2,
            },
            "async": {
                "srv": server.StartAsyncUdpServer,
                "cli": client.AsyncModbusUdpClient,
            },
            "sync": {
                "srv": "server.StartUdpServer",
                "cli": client.ModbusUdpClient,
            },
        },
    }

    cur = cfg[request]
    cur_m = cur[def_type]
    return cur_m["srv"], cur["srv_args"], cur_m["cli"], cur["cli_args"]


async def helper_start_async_server(comm):
    """Start async server"""
    run_server, server_args, _run_client, _client_args = helper_config(comm, "async")
    task = asyncio.create_task(run_server(**server_args))
    await asyncio.sleep(0.1)
    return task


async def helper_stop_async_server(task):
    """Stop async server"""
    await server.ServerAsyncStop()
    await task


async def helper_start_async_client(comm, check_connect=True):
    """Start async client"""
    _run_server, _server_args, run_client, client_args = helper_config(comm, "async")
    client = run_client(**client_args)
    await client.connect()
    await asyncio.sleep(0.1)
    if check_connect:
        assert client.protocol
    return client


async def helper_stop_async_client(test_client):
    """Stop async client"""
    await test_client.close()
    await asyncio.sleep(0)
    assert not test_client.protocol


async def helper_read_async(test_client):
    """Read async"""
    rr = await test_client.read_coils(1, 1, slave=0x01)
    assert len(rr.bits) == 8


def helper_start_sync_server(comm):
    """Start sync server"""
    run_server, server_args, _run_client, _client_args = helper_config(comm, "sync")
    proc = None
    return proc


def helper_stop_sync_server(_proc):
    """Stop sync server"""
    sleep(0.1)


def helper_start_sync_client(comm, _check_connect=True):
    """Start sync client"""
    _run_server, _server_args, run_client, client_args = helper_config(comm, "sync")
    client = None
    return client


def helper_stop_sync_client(_test_client):
    """Stop sync client"""


def helper_read_sync(test_client):
    """Read sync"""
    rr = test_client.read_coils(1, 1, slave=0x01)
    assert len(rr.bits) == 8


@pytest.mark.xdist_group(name="serial")
@pytest.mark.parametrize("comm", TEST_TYPES)
async def test_async_task_normal(comm):
    """Test normal client/server handling."""
    task = await helper_start_async_server(comm)
    client = await helper_start_async_client(comm)

    await helper_read_async(client)

    await helper_stop_async_client(client)
    await helper_stop_async_server(task)


@pytest.mark.xdist_group(name="serial")
@pytest.mark.parametrize("comm", TEST_TYPES)
async def test_async_task_reconnect(comm):
    """Test server stops."""
    if comm:
        return  # SKIP TEST FOR NOW
    if comm == "serial":
        return

    task = await helper_start_async_server(comm)
    client = await helper_start_async_client(comm)

    await helper_read_async(client)

    # restart server to break connection
    await helper_stop_async_server(task)

    # client must reconnect
    with pytest.raises(asyncio.exceptions.TimeoutError):
        await helper_read_async(client)

    await helper_stop_async_client(client)
    await helper_stop_async_server(task)


@pytest.mark.xdist_group(name="serial")
@pytest.mark.parametrize("comm", TEST_TYPES)
def test_sync_task_normal(comm):
    """Test normal client/server handling."""
    if comm:
        return  # SKIP TEST FOR NOW
    task = helper_start_sync_server(comm)
    client = helper_start_sync_client(comm)
    helper_read_sync(client)
    helper_stop_sync_client(client)
    helper_stop_sync_server(task)


@pytest.mark.xdist_group(name="serial")
@pytest.mark.parametrize("comm", TEST_TYPES)
async def test_sync_task_reconnect(comm):
    """Test server stops."""
    if comm:
        return  # SKIP TEST FOR NOW

    # JAN WAITING
    # Client does not clear client.protocol, timeout problem ?

    task = helper_start_sync_server(comm)
    client = helper_start_sync_client(comm)
    helper_read_sync(client)

    # Stop server before client, client must stop automatically
    helper_stop_sync_server(task)
    sleep(2)
    assert not client.protocol
    helper_stop_sync_client(client)
