"""Test client async."""
import asyncio
import logging
from dataclasses import dataclass
from threading import Thread
from time import sleep

import pytest
import pytest_asyncio

from examples.client_async import run_async_client, setup_async_client
from examples.client_calls import run_async_calls, run_sync_calls
from examples.client_payload import run_binary_payload_client
from examples.client_sync import run_sync_client, setup_sync_client
from examples.modbus_forwarder import setup_forwarder

# from examples.modbus_forwarder import run_forwarder, setup_forwarder
from examples.server_async import run_async_server, setup_server
from examples.server_payload import run_payload_server
from examples.server_sync import run_sync_server
from pymodbus import pymodbus_apply_logging_config
from pymodbus.client import AsyncModbusTcpClient
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


@dataclass
class Commandline:
    """Simulate commandline parameters."""

    comm = None
    framer = None
    port = None
    store = "sequential"
    slaves = None
    client_port = None
    client = None


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
    args = Commandline
    args.comm = test_comm
    args.framer = test_framer
    args.port = test_port + test_port_offset
    if test_comm == "serial":
        args.port = f"socket://127.0.0.1:{args.port}"
    run_args = setup_server(args)
    asyncio.create_task(run_async_server(run_args))
    await asyncio.sleep(0.1)
    yield
    await ServerAsyncStop()


async def run_client(test_comm, test_type, args=Commandline):
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
    if pytest.IS_WINDOWS and test_comm == "serial":
        return
    assert not mock_run_server
    args = Commandline
    args.framer = test_framer
    args.comm = test_comm
    args.port = test_port + test_port_offset
    await run_client(test_comm, None, args=args)


@pytest.mark.parametrize("test_port_offset", [20])
@pytest.mark.parametrize("test_comm, test_framer, test_port", [TEST_COMMS_FRAMER[0]])
def test_exp_sync_server_client(
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
):
    """Run sync client and server."""
    args = Commandline
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


@pytest.mark.parametrize("test_port_offset", [30])
@pytest.mark.parametrize("test_comm, test_framer, test_port", TEST_COMMS_FRAMER)
async def test_exp_client_calls(  # pylint: disable=unused-argument
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
    mock_run_server,
):
    """Test client-server async with different framers and calls."""
    if pytest.IS_WINDOWS:
        return
    if test_comm == "serial" and test_framer in (ModbusAsciiFramer, ModbusBinaryFramer):
        return
    if pytest.IS_WINDOWS and test_comm == "serial":
        return
    args = Commandline
    args.framer = test_framer
    args.comm = test_comm
    args.port = test_port + test_port_offset
    await run_client(test_comm, run_async_calls, args=args)


@pytest.mark.parametrize("test_port_offset", [40])
@pytest.mark.parametrize("test_comm, test_framer, test_port", [TEST_COMMS_FRAMER[0]])
async def test_exp_forwarder(  # pylint: disable=unused-argument
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
    mock_run_server,
):
    """Test modbus forwarder."""
    if pytest.IS_WINDOWS:
        return

    pymodbus_apply_logging_config()
    cmd_args = Commandline
    cmd_args.comm = test_comm
    cmd_args.framer = test_framer
    cmd_args.port = test_port + test_port_offset + 1
    cmd_args.client_port = test_port + test_port_offset
    run_args = setup_forwarder(cmd_args)
    # task = asyncio.create_task(run_forwarder(run_args))
    task = asyncio.create_task(run_async_server(run_args))
    await asyncio.sleep(0.1)

    real_client = AsyncModbusTcpClient(host="127.0.0.1", port=cmd_args.port)
    await real_client.connect()
    assert real_client.connected
    check_client = AsyncModbusTcpClient(host="127.0.0.1", port=cmd_args.client_port)
    await check_client.connect()
    assert check_client.connected
    await asyncio.sleep(0.1)

    # rr = _check_call(client.read_holding_registers(1, 1, slave=SLAVE))
    # rr = _check_call(client.read_coils(1, 1, slave=SLAVE))
    # rr = _check_call(client.read_discrete_inputs(0, 8, slave=SLAVE))
    # rr = _check_call(client.read_input_registers(1, 8, slave=SLAVE))
    # --
    # rr = _check_call(client.write_register(1, 10, slave=SLAVE))
    # rr = _check_call(client.write_coil(0, True, slave=SLAVE))
    # rr =_check_call(client.write_registers(1, [10] * 8, slave=SLAVE))
    # rr = _check_call(client.write_coils(1, [True] * 21, slave=SLAVE))

    # Verify read values are identical
    # rr_real = await real_client.read_holding_registers(1,1,slave=1)
    # assert rr_real.registers, f"---> {rr_real}"
    # rr_check = await check_client.read_holding_registers(1,1,slave=1)
    # assert rr_check.registers
    # assert rr_real.registers == rr_check.registers

    await real_client.close()
    await check_client.close()
    await asyncio.sleep(0.1)
    await ServerAsyncStop()
    await asyncio.sleep(0.1)
    task.cancel()


@pytest.mark.parametrize("test_port_offset", [50])
@pytest.mark.parametrize("test_comm, test_framer, test_port", [TEST_COMMS_FRAMER[0]])
async def test_exp_payload(  # pylint: disable=unused-argument
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
):
    """Test server/client with payload."""
    pymodbus_apply_logging_config()
    task = asyncio.create_task(run_payload_server(test_port + test_port_offset))
    await asyncio.sleep(0.1)
    await run_binary_payload_client(test_port + test_port_offset)
    await asyncio.sleep(0.1)
    await ServerAsyncStop()
    await asyncio.sleep(0.1)
    task.cancel()
