#!/usr/bin/env python3
"""Test performance of client: sync vs. async.

This example show how much faster the async version is.

example run:

(pymodbus) % ./client_performance.py
--- Testing sync client v3.4.1
running 1000 call (each 10 registers), took 114.10 seconds
Averages 114.10 ms pr call and 11.41 ms pr register.
--- Testing async client v3.4.1
running 1000 call (each 10 registers), took 0.33 seconds
Averages 0.33 ms pr call and 0.03 ms pr register.
"""
import asyncio
import time

from pymodbus import FramerType
from pymodbus.client import AsyncModbusSerialClient, ModbusSerialClient


LOOP_COUNT = 1000
REGISTER_COUNT = 10


def run_sync_client_test():
    """Run sync client."""
    print("--- Testing sync client v3.4.1")
    client = ModbusSerialClient(
        "/dev/ttys007",
        framer_name=FramerType.RTU,
        baudrate=9600,
    )
    client.connect()
    assert client.connected

    start_time = time.time()
    for _i in range(LOOP_COUNT):
        rr = client.read_input_registers(1, REGISTER_COUNT, slave=1)
        if rr.isError():
            print(f"Received Modbus library error({rr})")
            break
    client.close()
    run_time = time.time() - start_time
    avg_call = (run_time / LOOP_COUNT) * 1000
    avg_register = avg_call / REGISTER_COUNT
    print(
        f"running {LOOP_COUNT} call (each {REGISTER_COUNT} registers), took {run_time:.2f} seconds"
    )
    print(f"Averages {avg_call:.2f} ms pr call and {avg_register:.2f} ms pr register.")


async def run_async_client_test():
    """Run async client."""
    print("--- Testing async client v3.4.1")
    client = AsyncModbusSerialClient(
        "/dev/ttys007",
        framer_name=FramerType.RTU,
        baudrate=9600,
    )
    await client.connect()
    assert client.connected

    start_time = time.time()
    for _i in range(LOOP_COUNT):
        rr = await client.read_input_registers(1, REGISTER_COUNT, slave=1)
        if rr.isError():
            print(f"Received Modbus library error({rr})")
            break
    client.close()
    run_time = time.time() - start_time
    avg_call = (run_time / LOOP_COUNT) * 1000
    avg_register = avg_call / REGISTER_COUNT
    print(
        f"running {LOOP_COUNT} call (each {REGISTER_COUNT} registers), took {run_time:.2f} seconds"
    )
    print(f"Averages {avg_call:.2f} ms pr call and {avg_register:.2f} ms pr register.")


if __name__ == "__main__":
    run_sync_client_test()
    asyncio.run(run_async_client_test())
