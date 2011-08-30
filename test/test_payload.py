#!/usr/bin/env python
'''
Payload Utilities Test Fixture
--------------------------------
This fixture tests the functionality of the payload
utilities.

* PayloadBuilder
* PayloadDecoder
'''
import unittest
from pymodbus.constants import Endian
from pymodbus.payload import PayloadBuilder, PayloadDecoder

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class ModbusPayloadUtilityTests(unittest.TestCase):

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        '''
        Initializes the test environment and builds request/result
        encoding pairs
        '''
        self.little_endian_payload = \
                       '\x01\x02\x00\x03\x00\x00\x00\x04\x00\x00\x00\x00' \
                       '\x00\x00\x00\xff\xfe\xff\xfd\xff\xff\xff\xfc\xff' \
                       '\xff\xff\xff\xff\xff\xff\x00\x00\xa0\x3f\x00\x00' \
                       '\x00\x00\x00\x00\x19\x40\x74\x65\x73\x74'

        self.big_endian_payload = \
                       '\x01\x00\x02\x00\x00\x00\x03\x00\x00\x00\x00\x00' \
                       '\x00\x00\x04\xff\xff\xfe\xff\xff\xff\xfd\xff\xff' \
                       '\xff\xff\xff\xff\xff\xfc\x00\x00\xa0\x3f\x00\x00' \
                       '\x00\x00\x00\x00\x19\x40\x74\x65\x73\x74'

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    #-----------------------------------------------------------------------#
    # Payload Builder Tests
    #-----------------------------------------------------------------------#

    def testLittleEndianPayloadBuilder(self):
        ''' Test basic bit message encoding/decoding '''
        builder = PayloadBuilder(endian=Endian.Little)
        builder.add_8bit_uint(1)
        builder.add_16bit_uint(2)
        builder.add_32bit_uint(3)
        builder.add_64bit_uint(4)
        builder.add_8bit_int(-1)
        builder.add_16bit_int(-2)
        builder.add_32bit_int(-3)
        builder.add_64bit_int(-4)
        builder.add_32bit_float(1.25)
        builder.add_64bit_float(6.25)
        builder.add_string('test')
        self.assertEqual(self.little_endian_payload, builder.tostring())

    def testPayloadBuilderReset(self):
        ''' Test basic bit message encoding/decoding '''
        builder = PayloadBuilder()
        builder.add_8bit_uint(0x12)
        builder.add_8bit_uint(0x34)
        self.assertEqual('\x12\x34', builder.tostring())
        self.assertEqual(['\x12', '\x34'], builder.tolist())
        builder.reset()
        self.assertEqual('', builder.tostring())
        self.assertEqual([], builder.tolist())

    #-----------------------------------------------------------------------#
    # Payload Decoder Tests
    #-----------------------------------------------------------------------#

    def testLittleEndianPayloadDecoder(self):
        ''' Test basic bit message encoding/decoding '''
        decoder = PayloadDecoder(self.little_endian_payload)
        self.assertEqual(1,      decoder.decode_8bit_uint())
        self.assertEqual(2,      decoder.decode_16bit_uint())
        self.assertEqual(3,      decoder.decode_32bit_uint())
        self.assertEqual(4,      decoder.decode_64bit_uint())
        self.assertEqual(-1,     decoder.decode_8bit_int())
        self.assertEqual(-2,     decoder.decode_16bit_int())
        self.assertEqual(-3,     decoder.decode_32bit_int())
        self.assertEqual(-4,     decoder.decode_64bit_int())
        self.assertEqual(1.25,   decoder.decode_32bit_float())
        self.assertEqual(6.25,   decoder.decode_64bit_float())
        self.assertEqual('test', decoder.decode_string(4))

    def testPayloadDecoderReset(self):
        ''' Test the payload decoder reset functionality '''
        decoder = PayloadDecoder('\x12\x34')
        self.assertEqual(0x12, decoder.decode_8bit_uint())
        self.assertEqual(0x34, decoder.decode_8bit_uint())
        decoder.reset()   
        self.assertEqual(0x3412, decoder.decode_16bit_uint())


#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
