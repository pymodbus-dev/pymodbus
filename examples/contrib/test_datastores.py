#!/usr/bin/env python3
"""Test datastores compatibility.

Control that:

- ModbusSequentialDataBlock
- ModbusSparseDataBlock

Works as the used to work.

Control that SimData/SimDevice:

- works as intended in both shared and non shared mode.

Focussing on coils and discrete inputs.
"""
import asyncio

import pymodbus.client as modbusClient
from pymodbus import FramerType
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.logging import Log, pymodbus_apply_logging_config
from pymodbus.server import ServerAsyncStop, StartAsyncTcpServer
from pymodbus.transport import NULLMODEM_HOST


async def run_async(port, context, run_test):
    """Run server setup."""
    Log.info("### start ASYNC server")
    task = asyncio.create_task(StartAsyncTcpServer(
        context=context,
        address=(NULLMODEM_HOST, port),
        framer=FramerType.SOCKET
    ))
    await asyncio.sleep(1)

    Log.info("### Create client object")
    client = modbusClient.AsyncModbusTcpClient(
        NULLMODEM_HOST,
        port=5020,
        framer=FramerType.SOCKET,
    )
    await client.connect()
    await run_test(client)
    client.close()
    await ServerAsyncStop()
    task.cancel()
    await task


async def run_sequential(port) -> None:
    """Combine setup and run."""
    async def run_old_test(client):
        """Run test."""
        Log.info("### read_coils")
        single =  [True] + [False] * 7
        register = [True] * 7 + [False] * 8 + [True]
        rr = await client.read_coils(0, count=1, device_id=1)
        assert rr.bits == single
        rr = await client.read_coils(0, count=16, device_id=1)
        assert rr.bits == register
        rr = await client.read_discrete_inputs(0, count=1, device_id=1)
        assert rr.bits == single
        rr = await client.read_discrete_inputs(0, count=16, device_id=1)
        assert rr.bits == register

    co_data = [17] * 7 + [0] * 8 + [1]
    di_data = [True] * 7 + [False] * 8 + [True]
    context = ModbusServerContext(devices=ModbusDeviceContext(
        co=ModbusSequentialDataBlock(1, co_data),
        di=ModbusSequentialDataBlock(1, di_data),
        ),
        single=True
    )
    Log.info("Run sequential test.")
    await run_async(port, context, run_old_test)


async def run_all(port):
    """Run all tests."""
    pymodbus_apply_logging_config("info")
    await run_sequential(port)

if __name__ == "__main__":
    asyncio.run(run_all(5020), debug=True)
