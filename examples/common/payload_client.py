"""Pymodbus Client Payload Example.

This example shows how to build a client with a
complicated memory layout using builder-


Works out of the box together with payload_server.py
"""
from collections import OrderedDict
import logging

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #

FORMAT = (
    "%(asctime)-15s %(threadName)-15s"
    " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.INFO)

ORDER_DICT = {"<": "LITTLE", ">": "BIG"}


def run_binary_payload_client():
    """Run binary payload."""
    # ----------------------------------------------------------------------- #
    # We are going to use a simple sync client to send our requests
    # ----------------------------------------------------------------------- #
    client = ModbusClient("127.0.0.1", port=5020)
    client.connect()

    # ----------------------------------------------------------------------- #
    # If you need to build a complex message to send, you can use the payload
    # builder to simplify the packing logic
    #
    # Packing/unpacking depends on your CPU´s word/byte order. Modbus messages
    # are always using big endian. BinaryPayloadBuilder will pr default use
    # what your CPU uses.
    # The wordorder is applicable only for 32 and 64 bit values
    # Lets say we need to write a value 0x12345678 to a 32 bit register
    # The following combinations could be used to write the register
    # ++++++++++++++++++++++++++++++++++++++++++++ #
    # Word Order  | Byte order | Word1  | Word2  |
    # ------------+------------+--------+--------+
    #     Big     |     Big    | 0x1234 | 0x5678 |
    #     Big     |    Little  | 0x3412 | 0x7856 |
    #    Little   |     Big    | 0x5678 | 0x1234 |
    #    Little   |    Little  | 0x7856 | 0x3412 |
    # ++++++++++++++++++++++++++++++++++++++++++++ #

    # ----------------------------------------------------------------------- #
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
        # We can write registers
        client.write_registers(
            address,
            registers,
            unit=1)
        # Or we can write an encoded binary string
        client.write_registers(
            address,
            payload,
            skip_encode=True,
            unit=1
        )

        # ----------------------------------------------------------------------- #
        # If you need to decode a collection of registers in a weird layout, the
        # payload decoder can help you as well.
        # ----------------------------------------------------------------------- #
        print("Reading Registers:")
        address = 0x0
        count = len(payload)
        result = client.read_holding_registers(
            address,
            count,
            unit=1
        )
        print(result.registers)
        print("\n")
        decoder = BinaryPayloadDecoder.fromRegisters(
            result.registers,
            byteorder=byte_endian,
            wordorder=word_endian
        )
        # Make sure word/byte order is consistent between BinaryPayloadBuilder and BinaryPayloadDecoder
        assert decoder._byteorder == builder._byteorder  # nosec # pylint: disable=protected-access
        assert decoder._wordorder == builder._wordorder  # nosec # pylint: disable=protected-access

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
            print(
                "%s\t" % name,  # pylint: disable=consider-using-f-string
                hex(value)
                if isinstance(value, int)
                else value,
            )
        print("\n")

    # ----------------------------------------------------------------------- #
    # close the client
    # ----------------------------------------------------------------------- #
    client.close()


if __name__ == "__main__":
    run_binary_payload_client()
