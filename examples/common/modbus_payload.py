#!/usr/bin/env python
"""
Pymodbus Payload Building/Decoding Example
--------------------------------------------------------------------------

# Run modbus-payload-server.py or synchronous-server.py to check the behavior
"""
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.compat import iteritems

# --------------------------------------------------------------------------- # 
# configure the client logging
# --------------------------------------------------------------------------- # 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)


def run_binary_payload_ex():
    # ----------------------------------------------------------------------- #
    # We are going to use a simple client to send our requests
    # ----------------------------------------------------------------------- #
    client = ModbusClient('127.0.0.1', port=5440)
    client.connect()
    
    # ----------------------------------------------------------------------- #
    # If you need to build a complex message to send, you can use the payload
    # builder to simplify the packing logic.
    #
    # Here we demonstrate packing a random payload layout, unpacked it looks
    # like the following:
    #
    # - a 8 byte string 'abcdefgh'
    # - a 32 bit float 22.34
    # - a 16 bit unsigned int 0x1234
    # - another 16 bit unsigned int 0x5678
    # - an 8 bit int 0x12
    # - an 8 bit bitstring [0,1,0,1,1,0,1,0]
    # - an 32 bit uint 0x12345678
    # - an 32 bit signed int -0x1234
    # - an 64 bit signed int 0x12345678

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
    builder = BinaryPayloadBuilder(byteorder=Endian.Little,
                                   wordorder=Endian.Big)
    builder.add_string('abcdefgh')
    builder.add_32bit_float(22.34)
    builder.add_16bit_uint(0x1234)
    builder.add_16bit_uint(0x5678)
    builder.add_8bit_int(0x12)
    builder.add_bits([0, 1, 0, 1, 1, 0, 1, 0])
    builder.add_32bit_uint(0x12345678)
    builder.add_32bit_int(-0x1234)
    builder.add_64bit_int(0x1234567890ABCDEF)
    payload = builder.build()
    address = 0
    client.write_registers(address, payload, skip_encode=True, unit=1)
    # ----------------------------------------------------------------------- #
    # If you need to decode a collection of registers in a weird layout, the
    # payload decoder can help you as well.
    #
    # Here we demonstrate decoding a random register layout, unpacked it looks
    # like the following:
    #
    # - a 8 byte string 'abcdefgh'
    # - a 32 bit float 22.34
    # - a 16 bit unsigned int 0x1234
    # - another 16 bit unsigned int which we will ignore
    # - an 8 bit int 0x12
    # - an 8 bit bitstring [0,1,0,1,1,0,1,0]
    # ----------------------------------------------------------------------- #
    address = 0x00
    count = len(payload)
    result = client.read_holding_registers(address, count,  unit=1)
    print("-" * 60)
    print("Registers")
    print("-" * 60)
    print(result.registers)
    print("\n")
    decoder = BinaryPayloadDecoder.fromRegisters(result.registers,
                                                 byteorder=Endian.Little,
                                                 wordorder=Endian.Big)
    decoded = {
        'string': decoder.decode_string(8),
        'float': decoder.decode_32bit_float(),
        '16uint': decoder.decode_16bit_uint(),
        'ignored': decoder.skip_bytes(2),
        '8int': decoder.decode_8bit_int(),
        'bits': decoder.decode_bits(),
        "32uints": decoder.decode_32bit_uint(),
        "32ints": decoder.decode_32bit_int(),
        "64ints": decoder.decode_64bit_int(),
    }
    
    print("-" * 60)
    print("Decoded Data")
    print("-" * 60)
    for name, value in iteritems(decoded):
        print("%s\t" % name, hex(value) if isinstance(value, int) else value)
    
    # ----------------------------------------------------------------------- #
    # close the client
    # ----------------------------------------------------------------------- #
    client.close()


if __name__ == "__main__":
    run_binary_payload_ex()
