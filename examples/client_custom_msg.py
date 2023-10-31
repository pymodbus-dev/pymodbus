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

from pymodbus import Framer
from pymodbus.bit_read_message import ReadCoilsRequest
from pymodbus.client import AsyncModbusTcpClient as ModbusClient
from pymodbus.pdu import ModbusExceptions, ModbusRequest, ModbusResponse


# --------------------------------------------------------------------------- #
# create your custom message
# --------------------------------------------------------------------------- #
# The following is simply a read coil request that always reads 16 coils.
# Since the function code is already registered with the decoder factory,
# this will be decoded as a read coil response. If you implement a new
# method that is not currently implemented, you must register the request
# and response with a ClientDecoder factory.
# --------------------------------------------------------------------------- #


class CustomModbusResponse(ModbusResponse):  # pragma no cover
    """Custom modbus response."""

    function_code = 55
    _rtu_byte_count_pos = 2

    def __init__(self, values=None, **kwargs):
        """Initialize."""
        ModbusResponse.__init__(self, **kwargs)
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


class CustomModbusRequest(ModbusRequest):
    """Custom modbus request."""

    function_code = 55
    _rtu_frame_size = 8

    def __init__(self, address=None, **kwargs):
        """Initialize."""
        ModbusRequest.__init__(self, **kwargs)
        self.address = address
        self.count = 16

    def encode(self):
        """Encode."""
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data):  # pragma no cover
        """Decode."""
        self.address, self.count = struct.unpack(">HH", data)

    def execute(self, context):  # pragma no cover
        """Execute."""
        if not 1 <= self.count <= 0x7D0:
            return self.doException(ModbusExceptions.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(ModbusExceptions.IllegalAddress)
        values = context.getValues(self.function_code, self.address, self.count)
        return CustomModbusResponse(values)


# --------------------------------------------------------------------------- #
# This could also have been defined as
# --------------------------------------------------------------------------- #


class Read16CoilsRequest(ReadCoilsRequest):
    """Read 16 coils in one request."""

    def __init__(self, address, **kwargs):
        """Initialize a new instance.

        :param address: The address to start reading from
        """
        ReadCoilsRequest.__init__(self, address, 16, **kwargs)


# --------------------------------------------------------------------------- #
# execute the request with your client
# --------------------------------------------------------------------------- #
# using the with context, the client will automatically be connected
# and closed when it leaves the current scope.
# --------------------------------------------------------------------------- #


async def main(host="localhost", port=5020):
    """Run versions of read coil."""
    with ModbusClient(host=host, port=port, framer_name=Framer.SOCKET) as client:
        await client.connect()

        # new modbus function code.
        client.register(CustomModbusResponse)
        request = CustomModbusRequest(32, slave=1)
        result = await client.execute(request)
        print(result)

        # inherited request
        request = Read16CoilsRequest(32, slave=1)
        result = await client.execute(request)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())  # pragma: no cover
