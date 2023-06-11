"""Test examples to ensure they run"""
import asyncio
import logging

import pytest
import pytest_asyncio

from examples.server_async import run_async_server, setup_server
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
