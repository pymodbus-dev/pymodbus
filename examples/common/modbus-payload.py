#!/usr/bin/env python
'''
Pymodbus Payload Building/Decoding Example
--------------------------------------------------------------------------
'''
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

#---------------------------------------------------------------------------# 
# configure the client logging
#---------------------------------------------------------------------------# 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

#---------------------------------------------------------------------------# 
# We are going to use a simple client to send our requests
#---------------------------------------------------------------------------# 
client = ModbusClient('127.0.0.1')
client.connect()

#---------------------------------------------------------------------------# 
# If you need to build a complex message to send, you can use the payload
# builder to simplify the packing logic.
#
# Here we demonstrate packing a random payload layout, unpacked it looks
# like the following:
#
# - a 8 byte string 'abcdefgh'
# - a 32 bit float 22.34
# - a 16 bit unsigned int 0x1234
# - an 8 bit int 0x12
# - an 8 bit bitstring [0,1,0,1,1,0,1,0]
#---------------------------------------------------------------------------# 
builder = BinaryPayloadBuilder(endian=Endian.Little)
builder.add_string('abcdefgh')
builder.add_32bit_float(22.34)
builder.add_16bit_uint(0x1234)
builder.add_8bit_int(0x12)
builder.add_bits([0,1,0,1,1,0,1,0])
payload = builder.build()
address = 0x01
result  = client.write_registers(address, payload, skip_encode=True)

#---------------------------------------------------------------------------# 
# If you need to decode a collection of registers in a weird layout, the
# payload decoder can help you as well.
#
# Here we demonstrate decoding a random register layout, unpacked it looks
# like the following:
#
# - a 8 byte string 'abcdefgh'
# - a 32 bit float 22.34
# - a 16 bit unsigned int 0x1234
# - an 8 bit int 0x12
# - an 8 bit bitstring [0,1,0,1,1,0,1,0]
#---------------------------------------------------------------------------# 
address = 0x01
count   = 8
result  = client.read_input_registers(address, count)
decoder = BinaryPayloadDecoder.fromRegisters(result.registers, endian=Endian.Little)
decoded = {
    'string': decoder.decode_string(8),
    'float': decoder.decode_32bit_float(),
    '16uint': decoder.decode_16bit_uint(),
    '8int': decoder.decode_8bit_int(),
    'bits': decoder.decode_bits(),
}

print "-" * 60
print "Decoded Data"
print "-" * 60
for name, value in decoded.iteritems():
    print ("%s\t" % name), value

#---------------------------------------------------------------------------# 
# close the client
#---------------------------------------------------------------------------# 
client.close()
