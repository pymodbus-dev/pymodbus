#!/usr/bin/env python3
"""Pymodbus Client Payload Example.

This example shows how to build a client with a
complicated memory layout using builder-


Works out of the box together with payload_server.py
"""
import asyncio
import logging
from collections import OrderedDict

from examples.client_async import run_async_client, setup_async_client
from examples.helper import get_commandline
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder


_logger = logging.getLogger()
ORDER_DICT = {"<": "LITTLE", ">": "BIG"}


async def run_payload_calls(client):
    """Run binary payload.

    If you need to build a complex message to send, you can use the payload
    builder to simplify the packing logic

    Packing/unpacking depends on your CPU's word/byte order. Modbus messages
    are always using big endian. BinaryPayloadBuilder will per default use
    what your CPU uses.
    The wordorder is applicable only for 32 and 64 bit values
    Lets say we need to write a value 0x12345678 to a 32 bit register
    The following combinations could be used to write the register
    ++++++++++++++++++++++++++++++++++++++++++++
    Word Order  | Byte order | Word1  | Word2  |
    ------------+------------+--------+--------+
        Big     |     Big    | 0x1234 | 0x5678 |
        Big     |    Little  | 0x3412 | 0x7856 |
       Little   |     Big    | 0x5678 | 0x1234 |
       Little   |    Little  | 0x7856 | 0x3412 |
    ++++++++++++++++++++++++++++++++++++++++++++
    """
    for word_endian, byte_endian in (
        (Endian.Big, Endian.Big),
        (Endian.Big, Endian.Little),
        (Endian.Little, Endian.Big),
        (Endian.Little, Endian.Little),
    ):
        print("-" * 60)
        print(f"Word Order: {ORDER_DICT[word_endian]}")
        print(f"Byte Order: {ORDER_DICT[byte_endian]}")
        print()
        builder = BinaryPayloadBuilder(
            wordorder=word_endian,
            byteorder=byte_endian,
        )
        # Normally just do:  builder = BinaryPayloadBuilder()
        my_string = "abcdefgh"
        builder.add_string(my_string)
        builder.add_bits([0, 1, 0, 1, 1, 0, 1, 0])
        builder.add_8bit_int(-0x12)
        builder.add_8bit_uint(0x12)
        builder.add_16bit_int(-0x5678)
        builder.add_16bit_uint(0x1234)
        builder.add_32bit_int(-0x1234)
        builder.add_32bit_uint(0x12345678)
        builder.add_16bit_float(12.34)
        builder.add_16bit_float(-12.34)
        builder.add_32bit_float(22.34)
        builder.add_32bit_float(-22.34)
        builder.add_64bit_int(-0xDEADBEEF)
        builder.add_64bit_uint(0x12345678DEADBEEF)
        builder.add_64bit_uint(0x12345678DEADBEEF)
        builder.add_64bit_float(123.45)
        builder.add_64bit_float(-123.45)
        registers = builder.to_registers()
        print("Writing Registers:")
        print(registers)
        print("\n")
        payload = builder.build()
        address = 0
        slave = 1
        # We can write registers
        rr = await client.write_registers(address, registers, slave=slave)
        assert not rr.isError()
        # Or we can write an encoded binary string
        rr = await client.write_registers(address, payload, skip_encode=True, slave=1)
        assert not rr.isError()

        # ----------------------------------------------------------------------- #
        # If you need to decode a collection of registers in a weird layout, the
        # payload decoder can help you as well.
        # ----------------------------------------------------------------------- #
        print("Reading Registers:")
        count = len(payload)
        rr = await client.read_holding_registers(address, count, slave=slave)
        assert not rr.isError()
        print(rr.registers)
        print("\n")
        decoder = BinaryPayloadDecoder.fromRegisters(
            rr.registers, byteorder=byte_endian, wordorder=word_endian
        )
        # Make sure word/byte order is consistent between BinaryPayloadBuilder and BinaryPayloadDecoder
        assert (
            decoder._byteorder == builder._byteorder  # pylint: disable=protected-access
        )  # nosec
        assert (
            decoder._wordorder == builder._wordorder  # pylint: disable=protected-access
        )  # nosec

        decoded = OrderedDict(
            [
                ("string", decoder.decode_string(len(my_string))),
                ("bits", decoder.decode_bits()),
                ("8int", decoder.decode_8bit_int()),
                ("8uint", decoder.decode_8bit_uint()),
                ("16int", decoder.decode_16bit_int()),
                ("16uint", decoder.decode_16bit_uint()),
                ("32int", decoder.decode_32bit_int()),
                ("32uint", decoder.decode_32bit_uint()),
                ("16float", decoder.decode_16bit_float()),
                ("16float2", decoder.decode_16bit_float()),
                ("32float", decoder.decode_32bit_float()),
                ("32float2", decoder.decode_32bit_float()),
                ("64int", decoder.decode_64bit_int()),
                ("64uint", decoder.decode_64bit_uint()),
                ("ignore", decoder.skip_bytes(8)),
                ("64float", decoder.decode_64bit_float()),
                ("64float2", decoder.decode_64bit_float()),
            ]
        )
        print("Decoded Data")
        for name, value in iter(decoded.items()):
            print(f"{name}\t{hex(value) if isinstance(value, int) else value}")
        print("\n")


if __name__ == "__main__":
    cmd_args = get_commandline(
        description="Run payload client.",
    )
    testclient = setup_async_client(cmd_args)
    asyncio.run(run_async_client(testclient, modbus_calls=run_payload_calls))
