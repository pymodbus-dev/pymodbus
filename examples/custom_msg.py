#!/usr/bin/env python3
# pylint: disable=missing-type-doc
"""Pymodbus Synchronous Client Examples.

The following is an example of how to use the synchronous modbus client
implementation from pymodbus::

    with ModbusClient("127.0.0.1") as client:
        result = client.read_coils(1,10)
        print result

"""
import asyncio
import struct

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient as ModbusClient
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import ModbusPDU
from pymodbus.pdu.bit_message import ReadCoilsRequest
from pymodbus.server import ServerAsyncStop, StartAsyncTcpServer


# --------------------------------------------------------------------------- #
# create your custom message
# --------------------------------------------------------------------------- #
# The following is simply a read coil request that always reads 16 coils.
# Since the function code is already registered with the decoder factory,
# this will be decoded as a read coil response. If you implement a new
# method that is not currently implemented, you must register the request
# and response with the active DecodePDU object.
# --------------------------------------------------------------------------- #


class CustomModbusResponse(ModbusPDU):
    """Custom modbus response."""

    function_code = 55
    rtu_byte_count_pos = 2

    def __init__(self, values=None, slave=1, transaction=0):
        """Initialize."""
        super().__init__(dev_id=slave, transaction_id=transaction)
        self.values = values or []

    def encode(self):
        """Encode response pdu.

        :returns: The encoded packet message
        """
        res = struct.pack(">B", len(self.values) * 2)
        for register in self.values:
            res += struct.pack(">H", register)
        return res

    def decode(self, data):
        """Decode response pdu.

        :param data: The packet data to decode
        """
        byte_count = int(data[0])
        self.values = []
        for i in range(1, byte_count + 1, 2):
            self.values.append(struct.unpack(">H", data[i : i + 2])[0])


class CustomRequest(ModbusPDU):
    """Custom modbus request."""

    function_code = 55
    rtu_frame_size = 8

    def __init__(self, address=None, slave=1, transaction=0):
        """Initialize."""
        super().__init__(dev_id=slave, transaction_id=transaction)
        self.address = address
        self.count = 2

    def encode(self):
        """Encode."""
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data):
        """Decode."""
        self.address, self.count = struct.unpack(">HH", data)

    async def update_datastore(self, context: ModbusSlaveContext) -> ModbusPDU:
        """Execute."""
        _ = context
        return CustomModbusResponse()


# --------------------------------------------------------------------------- #
# This could also have been defined as
# --------------------------------------------------------------------------- #


class Read16CoilsRequest(ReadCoilsRequest):
    """Read 16 coils in one request."""

    def __init__(self, address, slave=1, transaction=0):
        """Initialize a new instance.

        :param address: The address to start reading from
        """
        super().__init__(address=address, count=16, dev_id=slave, transaction_id=transaction)


# --------------------------------------------------------------------------- #
# execute the request with your client
# --------------------------------------------------------------------------- #
# using the with context, the client will automatically be connected
# and closed when it leaves the current scope.
# --------------------------------------------------------------------------- #


async def main(host="localhost", port=5020):
    """Run versions of read coil."""
    store = ModbusServerContext(slaves=ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [17] * 100),
            co=ModbusSequentialDataBlock(0, [17] * 100),
            hr=ModbusSequentialDataBlock(0, [17] * 100),
            ir=ModbusSequentialDataBlock(0, [17] * 100),
        ),
        single=True
    )
    task = asyncio.create_task(StartAsyncTcpServer(
        context=store,
        address=(host, port),
        custom_pdu=[CustomRequest])
    )
    await asyncio.sleep(0.1)
    async with ModbusClient(host=host, port=port, framer=FramerType.SOCKET) as client:
        await client.connect()

        # add new modbus function code.
        client.register(CustomModbusResponse)
        slave=1
        request1 = CustomRequest(32, slave=slave)
        try:
            result = await client.execute(False, request1)
        except ModbusIOException:
            print("Server do not support CustomRequest.")
        else:
            print(result)

        # inherited request
        request2 = Read16CoilsRequest(32, slave)
        result = await client.execute(False, request2)
        print(result)
    await ServerAsyncStop()
    task.cancel()
    await task


if __name__ == "__main__":
    asyncio.run(main())
