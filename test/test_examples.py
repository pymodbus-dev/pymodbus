"""Test examples to ensure they run

the following are excluded:
    client_async.py
    client_calls.py
    client_sync.py
    helper.py
    server_async.py
    server_sync.py

they represent generic examples and
are tested in
    test_example_client_server.py
a lot more thoroughly.
"""
import asyncio
import logging

import pytest
import pytest_asyncio

from examples.build_bcd_payload import BcdPayloadBuilder, BcdPayloadDecoder
from examples.client_async import run_async_client, setup_async_client
from examples.client_custom_msg import run_custom_client
from examples.client_payload import run_payload_calls
from examples.client_test import run_async_calls as run_client_test
from examples.datastore_simulator import run_server_simulator, setup_simulator
from examples.message_generator import generate_messages
from examples.message_parser import parse_messages
from examples.server_async import run_async_server, setup_server
from examples.server_callback import run_callback_server
from examples.server_payload import setup_payload_server
from examples.server_updating import run_updating_server, setup_updating_server
from pymodbus import pymodbus_apply_logging_config
from pymodbus.server import ServerAsyncStop


# from examples.serial_forwarder import run_forwarder


_logger = logging.getLogger()
_logger.setLevel("DEBUG")
pymodbus_apply_logging_config("DEBUG")


CMDARGS = [
    "--comm",
    "tcp",
    "--port",
    "5020",
    "--baudrate",
    "9600",
    "--log",
    "debug",
    "--framer",
    "socket",
]


@pytest_asyncio.fixture(name="mock_run_server")
async def _helper_server():
    """Run server."""
    run_args = setup_server(cmdline=CMDARGS)
    task = asyncio.create_task(run_async_server(run_args))
    await asyncio.sleep(0.1)
    yield
    await ServerAsyncStop()
    await asyncio.sleep(0.1)
    task.cancel()
    await task
    await asyncio.sleep(0.1)


@pytest.mark.xdist_group(name="server_serialize")
async def test_exp_server_client_payload():
    """Test server/client with payload."""
    run_args = setup_payload_server(cmdline=CMDARGS)
    task = asyncio.create_task(run_async_server(run_args))
    await asyncio.sleep(0.1)
    testclient = setup_async_client(cmdline=CMDARGS)
    await run_async_client(testclient, modbus_calls=run_payload_calls)
    await asyncio.sleep(0.1)
    await ServerAsyncStop()
    await asyncio.sleep(0.1)
    task.cancel()
    await task


@pytest.mark.xdist_group(name="server_serialize")
async def test_exp_client_test(mock_run_server):
    """Test client used for fast testing."""
    assert not mock_run_server

    testclient = setup_async_client(cmdline=CMDARGS)
    await run_async_client(testclient, modbus_calls=run_client_test)


@pytest.mark.parametrize("framer", ["socket", "rtu"])
async def test_exp_message_generator(framer):
    """Test all message generator."""
    generate_messages(cmdline=["--framer", framer])


@pytest.mark.xdist_group(name="server_serialize")
async def test_exp_server_simulator():
    """Test server simulator."""
    cmdargs = ["--log", "debug", "--port", "5020"]
    run_args = setup_simulator(cmdline=cmdargs)
    task = asyncio.create_task(run_server_simulator(run_args))
    await asyncio.sleep(0.1)
    testclient = setup_async_client(cmdline=CMDARGS)
    await run_async_client(testclient, modbus_calls=run_client_test)
    await asyncio.sleep(0.1)
    await ServerAsyncStop()
    await asyncio.sleep(0.1)
    task.cancel()
    await task


@pytest.mark.xdist_group(name="server_serialize")
async def test_exp_updating_server():
    """Test server simulator."""
    run_args = setup_updating_server(cmdline=CMDARGS)
    task = asyncio.create_task(run_updating_server(run_args))
    await asyncio.sleep(0.1)
    testclient = setup_async_client(cmdline=CMDARGS)
    await run_async_client(testclient, modbus_calls=run_client_test)
    await asyncio.sleep(0.1)
    await ServerAsyncStop()
    await asyncio.sleep(0.1)
    task.cancel()
    await task


def test_exp_build_bcd_payload():
    """Test build bcd payload."""
    builder = BcdPayloadBuilder()
    decoder = BcdPayloadDecoder(builder)
    assert str(decoder)


def test_exp_message_parser():
    """Test message parser."""
    parse_messages(["--framer", "socket", "-m", "000100000006010100200001"])
    parse_messages(["--framer", "socket", "-m", "00010000000401010101"])


@pytest.mark.xdist_group(name="server_serialize")
async def test_exp_server_callback():
    """Test server/client with payload."""
    task = asyncio.create_task(run_callback_server(cmdline=CMDARGS))
    await asyncio.sleep(0.1)
    testclient = setup_async_client(cmdline=CMDARGS)
    await run_async_client(testclient, modbus_calls=run_client_test)
    await asyncio.sleep(0.1)
    await ServerAsyncStop()
    await asyncio.sleep(0.1)
    task.cancel()
    await task


@pytest.mark.xdist_group(name="server_serialize")
async def test_exp_client_custom_msg(mock_run_server):
    """Test client with custom message."""
    assert not mock_run_server

    run_custom_client()


# to be updated:
#   modbus_forwarder.py
#
# to be converted:
#   v2.5.3


# @pytest.mark.parametrize("test_port_offset", [40])
# @pytest.mark.parametrize("test_comm, test_framer, test_port", [TEST_COMMS_FRAMER[0]])
async def xtest_exp_forwarder(
    test_comm,
    test_framer,
    test_port_offset,
    test_port,
    mock_run_server,
):
    """Test modbus forwarder."""
    assert not mock_run_server
    if pytest.IS_WINDOWS:
        return
    print(test_comm, test_framer, test_port_offset, test_port)
    # cmd_args.comm = test_comm
    # cmd_args.framer = test_framer
    # cmd_args.port = test_port + test_port_offset + 1
    # cmd_args.client_port = test_port + test_port_offset
    # task = asyncio.create_task(run_forwarder(cmd_args))
    # await asyncio.sleep(0.1)
    # real_client = AsyncModbusTcpClient(host=cmd_args.host, port=cmd_args.port)
    # await real_client.connect()
    # assert real_client.connected
    # check_client = AsyncModbusTcpClient(host=cmd_args.host, port=cmd_args.client_port)
    # await check_client.connect()
    # assert check_client.connected
    # await asyncio.sleep(0.1)

    # rr = await check_client.read_holding_registers(1, 1, slave=1)
    # rq = await real_client.read_holding_registers(1, 1, slave=1)
    # assert rr.registers
    # assert rq.registers
    # rr = await check_client.read_coils(1, 1, slave=1)
    # assert rr.bits
    # rr = await check_client.read_discrete_inputs(1, 1, slave=1)
    # assert rr.bits
    # rr = await check_client.read_input_registers(1, 1, slave=1)
    # assert rr.registers

    # --
    # rr = _check_call(check_client.write_register(1, 10, slave=1))
    # rr = _check_call(check_client.write_coil(0, True, slave=1))
    # rr =_check_call(check_client.write_registers(1, [10] * 8, slave=1))
    # rr = _check_call(check_client.write_coils(1, [True] * 21, slave=1))

    # Verify read values are identical
    # rr_real = await real_client.read_holding_registers(1,1,slave=1)
    # assert rr_real.registers, f"---> {rr_real}"

    # await real_client.close()
    # await check_client.close()
    # await asyncio.sleep(0.1)
    # await ServerAsyncStop()
    # await asyncio.sleep(0.1)
    # task.cancel()
