from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
from pymodbus.client.asynchronous import schedulers

import trio


async def main():
    client = ModbusClient(scheduler=schedulers.TRIO, host="127.0.0.1", port=5020)

    async with client.manage_connection() as protocol:
        # print(await protocol.read_coils(address=1, count=1, unit=0x01))
        print(await protocol.read_holding_registers(address=1, count=1, unit=0x01))
        # print(await protocol.read_holding_registers(address=10, count=1, unit=0x01))

trio.run(main)
