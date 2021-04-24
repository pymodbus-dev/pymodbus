#!/usr/bin/env python
"""
Pymodbus Asynchronous Client Examples
--------------------------------------------------------------------------

The following is an example of how to use the asynchronous modbus
client implementation from pymodbus with Trio.

The example is only valid on Python3.6 and above
"""
import contextlib
import logging
import sys

from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
from pymodbus.client.asynchronous import schedulers

import trio


async def main():
    root_logger = logging.getLogger()
    handler = logging.StreamHandler(stream=sys.stdout)
    root_logger.addHandler(hdlr=handler)
    root_logger.setLevel(logging.DEBUG)

    client = ModbusClient(scheduler=schedulers.TRIO, host="127.0.0.1", port=5020)

    with contextlib.suppress(KeyboardInterrupt):
        async with client.manage_connection() as protocol:
            while True:
                response = await protocol.read_coils(address=1, count=1, unit=0x01)
                print('  response:', response.bits)
                response = await protocol.read_holding_registers(address=1, count=1, unit=0x01)
                print('  response:', response.registers)
                response = await protocol.read_holding_registers(address=10, count=1, unit=0x01)
                print('  response:', response.registers)

                await trio.sleep(1)


trio.run(main)
