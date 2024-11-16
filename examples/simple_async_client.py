#!/usr/bin/env python3
"""Pymodbus asynchronous client example.

An example of a single threaded synchronous client.

usage: simple_async_client.py

All options must be adapted in the code
The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""
import asyncio

import pymodbus.client as ModbusClient
from pymodbus import (
    FramerType,
    ModbusException,
    pymodbus_apply_logging_config,
)


async def run_async_simple_client(comm, host, port, framer=FramerType.SOCKET):
    """Run async client."""
    # activate debugging
    pymodbus_apply_logging_config("DEBUG")

    print("get client")
    client: ModbusClient.ModbusBaseClient
    if comm == "tcp":
        client = ModbusClient.AsyncModbusTcpClient(
            host,
            port=port,
            framer=framer,
            # timeout=10,
            # retries=3,
            # source_address=("localhost", 0),
        )
    elif comm == "udp":
        client = ModbusClient.AsyncModbusUdpClient(
            host,
            port=port,
            framer=framer,
            # timeout=10,
            # retries=3,
            # source_address=None,
        )
    elif comm == "serial":
        client = ModbusClient.AsyncModbusSerialClient(
            port,
            framer=framer,
            # timeout=10,
            # retries=3,
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            # handle_local_echo=False,
        )
    else:
        print(f"Unknown client {comm} selected")
        return

    print("connect to server")
    await client.connect()
    # test client is connected
    assert client.connected

    print("get and verify data")
    try:
        # See all calls in client_calls.py
        rr = await client.read_coils(1, count=1, slave=1)
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
        client.close()
        return
    if rr.isError():
        print(f"Received exception from device ({rr})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        client.close()
        return
    try:
        # See all calls in client_calls.py
        rr = await client.read_holding_registers(10, count=2, slave=1)
    except ModbusException as exc:
        print(f"Received ModbusException({exc}) from library")
        client.close()
        return
    if rr.isError():
        print(f"Received exception from device ({rr})")
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        client.close()
        return
    value_int32 = client.convert_from_registers(rr.registers, data_type=client.DATATYPE.INT32)
    print(f"Got int32: {value_int32}")
    print("close connection")
    client.close()


if __name__ == "__main__":
    asyncio.run(
        run_async_simple_client("tcp", "127.0.0.1", 5020), debug=True
    )
