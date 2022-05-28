#!/usr/bin/env python3
"""Pymodbus Payload Building/Decoding Example.

# Run modbus_payload_server.py or synchronous_server.py to check the behavior
"""
import logging
from collections import OrderedDict

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #

FORMAT = (
    "%(asctime)-15s %(threadName)-15s"
    " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)  # NOSONAR
log = logging.getLogger()
log.setLevel(logging.INFO)

ORDER_DICT = {"<": "LITTLE", ">": "BIG"}


def run_binary_payload_ex():
    """Run binary payload."""
    # ----------------------------------------------------------------------- #
    # We are going to use a simple client to send our requests
    # ----------------------------------------------------------------------- #
    client = ModbusClient("127.0.0.1", port=5020)
    client.connect()

    # ----------------------------------------------------------------------- #
    # If you need to build a complex message to send, you can use the payload
    # builder to simplify the packing logic.
    #
    # Here we demonstrate packing a random payload layout, unpacked it looks
    # like the following:
    #
    # - an 8 byte string "abcdefgh"
    # - an 8 bit bitstring [0,1,0,1,1,0,1,0]
    # - an 8 bit int -0x12
    # - an 8 bit unsigned int 0x12
    # - a 16 bit int -0x5678
    # - a 16 bit unsigned int 0x1234
    # - a 32 bit int -0x1234
    # - a 32 bit unsigned int 0x12345678
    # - a 16 bit float 12.34
    # - a 16 bit float -12.34
    # - a 32 bit float 22.34
    # - a 32 bit float -22.34
    # - a 64 bit int -0xDEADBEEF
    # - a 64 bit unsigned int 0x12345678DEADBEEF
    # - another 64 bit unsigned int 0x12345678DEADBEEF
    # - a 64 bit float 123.45
    # - a 64 bit float -123.45

    # The packing can also be applied to the word (wordorder) and bytes in each
    # word (byteorder)

    # The wordorder is applicable only for 32 and 64 bit values
    # Lets say we need to write a value 0x12345678 to a 32 bit register

    # The following combinations could be used to write the register

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #
    # Word Order - Big                      Byte Order - Big
    # word1 =0x1234 word2 = 0x5678

    # Word Order - Big                      Byte Order - Little
    # word1 =0x3412 word2 = 0x7856

    # Word Order - Little                   Byte Order - Big
    # word1 = 0x5678 word2 = 0x1234

    # Word Order - Little                   Byte Order - Little
    # word1 =0x7856 word2 = 0x3412
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ #

    # ----------------------------------------------------------------------- #
    combos = [
        (word_endian, byte_endian)
        for word_endian in (Endian.Big, Endian.Little)
        for byte_endian in (Endian.Big, Endian.Little)
    ]
    for word_endian, byte_endian in combos:
        print("-" * 60)
        print(f"Word Order: {ORDER_DICT[word_endian]}")
        print(f"Byte Order: {ORDER_DICT[byte_endian]}")
        print()
        builder = BinaryPayloadBuilder(byteorder=byte_endian, wordorder=word_endian)
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
        payload = builder.to_registers()
        print("-" * 60)
        print("Writing Registers")
        print("-" * 60)
        print(payload)
        print("\n")
        payload = builder.build()
        address = 0
        # Can write registers
        # registers = builder.to_registers()
        # client.write_registers(address, registers, unit=1)

        # Or can write encoded binary string
        client.write_registers(address, payload, skip_encode=True, unit=1)
        # ----------------------------------------------------------------------- #
        # If you need to decode a collection of registers in a weird layout, the
        # payload decoder can help you as well.
        #
        # Here we demonstrate decoding a random register layout, unpacked it looks
        # like the following:
        #
        # - an 8 byte string "abcdefgh"
        # - an 8 bit bitstring [0,1,0,1,1,0,1,0]
        # - an 8 bit int -0x12
        # - an 8 bit unsigned int 0x12
        # - a 16 bit int -0x5678
        # - a 16 bit unsigned int 0x1234
        # - a 32 bit int -0x1234
        # - a 32 bit unsigned int 0x12345678
        # - a 16 bit float 12.34
        # - a 16 bit float -12.34
        # - a 32 bit float 22.34
        # - a 32 bit float -22.34
        # - a 64 bit int -0xDEADBEEF
        # - a 64 bit unsigned int 0x12345678DEADBEEF
        # - another 64 bit unsigned int which we will ignore
        # - a 64 bit float 123.45
        # - a 64 bit float -123.45
        # ----------------------------------------------------------------------- #
        address = 0x0
        count = len(payload)
        result = client.read_holding_registers(address, count, unit=1)
        print("-" * 60)
        print("Registers")
        print("-" * 60)
        print(result.registers)
        print("\n")
        decoder = BinaryPayloadDecoder.fromRegisters(
            result.registers, byteorder=byte_endian, wordorder=word_endian
        )

        assert decoder._byteorder == (  # nosec # pylint: disable=protected-access
            builder._byteorder,  # nosec # pylint: disable=protected-access
            "Make sure byteorder is consistent between BinaryPayloadBuilder and BinaryPayloadDecoder",
        )

        assert decoder._wordorder == (  # nosec # pylint: disable=protected-access
            builder._wordorder,  # nosec # pylint: disable=protected-access
            "Make sure wordorder is consistent between BinaryPayloadBuilder and BinaryPayloadDecoder",
        )

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

        print("-" * 60)
        print("Decoded Data")
        print("-" * 60)
        for name, value in iter(decoded.items()):
            print(
                "%s\t" % name,  # pylint: disable=consider-using-f-string
                hex(value)
                if isinstance(value, int)
                else value,
            )

    # ----------------------------------------------------------------------- #
    # close the client
    # ----------------------------------------------------------------------- #
    client.close()


if __name__ == "__main__":
    run_binary_payload_ex()
