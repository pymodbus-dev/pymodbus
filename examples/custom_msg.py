#!/usr/bin/env python3
"""Pymodbus Synchronous Client Examples.

The following is an example of how to use the synchronous modbus client
implementation from pymodbus::

    with ModbusClient("127.0.0.1") as client:
        result = client.read_coils(1,10)
        print result

"""

import asyncio

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient as ModbusClient
from pymodbus.server import ServerAsyncStop, StartAsyncTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice


# --------------------------------------------------------------------------- #
# create your custom message
# --------------------------------------------------------------------------- #
# The following is simply a read coil request that always reads 16 coils.
# Since the function code is already registered with the decoder,
# this will be decoded as a read coil response. If you implement a new
# method that is not currently implemented, you must register the request
# and response with the active DecodePDU object.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# execute the request with your client
# --------------------------------------------------------------------------- #
# using the with context, the client will automatically be connected
# and closed when it leaves the current scope.
# --------------------------------------------------------------------------- #


async def main(host="localhost", port=5020):
    """Run versions of read coil."""
    task = asyncio.create_task(
        StartAsyncTcpServer(
            context=SimDevice(
                0, SimData(0, datatype=DataType.REGISTERS, values=[17] * 100)
            ),
            address=(host, port),
        )
    )
    await asyncio.sleep(0.1)
    async with ModbusClient(host=host, port=port, framer=FramerType.SOCKET) as client:
        await client.connect()

        # add new modbus function code.
    await ServerAsyncStop()
    task.cancel()
    await task


if __name__ == "__main__":
    asyncio.run(main())
