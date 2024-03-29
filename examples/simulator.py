#!/usr/bin/env python3
"""Pymodbus simulator server/client Example.

An example of how to use the simulator (server) with a client.

for usage see documentation of simulator

.. tip:: pymodbus.simulator starts the server directly from the commandline
"""
import asyncio
import logging

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.datastore import ModbusSimulatorContext
from pymodbus.server import ModbusSimulatorServer, get_simulator_commandline


_logger = logging.getLogger(__file__)


async def read_registers(
    client, addr, count, is_int, curval=None, minval=None, maxval=None
):
    """Run modbus call."""
    rr = await client.read_holding_registers(addr, count, slave=1)
    assert not rr.isError()
    if count == 1:
        value = rr.registers[0]
    else:
        value = ModbusSimulatorContext.build_value_from_registers(rr.registers, is_int)
        if not is_int:
            value = round(value, 1)
    if curval:
        assert value == curval, f"{value} == {curval}"
    else:
        assert minval <= value <= maxval, f"{minval} <= {value} <= {maxval}"


async def run_calls(client, count):
    """Run client calls."""
    _logger.info("### Read fixed/increment/random value of different types.")
    _logger.info("--> UINT16")
    for count in range(1, 5):
        await read_registers(client, 1148, 1, True, curval=32117)
        await read_registers(client, 2305, 1, True, curval=50 + count)
        await read_registers(client, 2306, 1, True, minval=45, maxval=55)

        _logger.info("--> UINT32")
        await read_registers(client, 3188, 2, True, curval=32514)
        await read_registers(client, 3876, 2, True, curval=50000 + count)
        await read_registers(client, 3878, 2, True, minval=45000, maxval=55000)

        _logger.info("--> FLOAT32")
        await read_registers(client, 4188, 2, False, curval=32514.2)
        await read_registers(client, 4876, 2, False, curval=50000.0 + count)
        await read_registers(client, 4878, 2, False, minval=45000.0, maxval=55000.0)


async def run_simulator():
    """Run server."""
    _logger.info("### start server simulator")
    cmdline = [
        "--modbus_device",
        "device_try",
        "--modbus_server",
        "server",
    ]
    cmd_args = get_simulator_commandline(cmdline=cmdline)
    task = ModbusSimulatorServer(**cmd_args)
    await task.run_forever(only_start=True)

    _logger.info("### start client")
    client = AsyncModbusTcpClient(
        "127.0.0.1",
        port=5020,
        framer=FramerType.SOCKET,
    )
    await client.connect()
    assert client.connected

    _logger.info("### run calls")
    await run_calls(client, 1)

    _logger.info("### shutdown client")
    client.close()

    _logger.info("### shutdown server")
    await task.stop()
    _logger.info("### Thanks for now.")


if __name__ == "__main__":
    asyncio.run(run_simulator(), debug=True)
