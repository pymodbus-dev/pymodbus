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
from pymodbus.exceptions import ParameterException
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
                       '\x00\x00\x00\x00\x19\x40\x74\x65\x73\x74\x11'

        self.big_endian_payload = \
                       '\x01\x00\x02\x00\x00\x00\x03\x00\x00\x00\x00\x00' \
                       '\x00\x00\x04\xff\xff\xfe\xff\xff\xff\xfd\xff\xff' \
                       '\xff\xff\xff\xff\xff\xfc\x3f\xa0\x00\x00\x40\x19' \
                       '\x00\x00\x00\x00\x00\x00\x74\x65\x73\x74\x11'

        self.bitstring = [True, False, False, False, True, False, False, False]

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
        builder.add_bits(self.bitstring)
        self.assertEqual(self.little_endian_payload, builder.tostring())

    def testBigEndianPayloadBuilder(self):
        ''' Test basic bit message encoding/decoding '''
        builder = PayloadBuilder(endian=Endian.Big)
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
        builder.add_bits(self.bitstring)
        self.assertEqual(self.big_endian_payload, builder.tostring())

    def testPayloadBuilderReset(self):
        ''' Test basic bit message encoding/decoding '''
        builder = PayloadBuilder()
        builder.add_8bit_uint(0x12)
        builder.add_8bit_uint(0x34)
        builder.add_8bit_uint(0x56)
        builder.add_8bit_uint(0x78)
        self.assertEqual('\x12\x34\x56\x78', builder.tostring())
        self.assertEqual(['\x12\x34', '\x56\x78'], builder.tolist())
        builder.reset()
        self.assertEqual('', builder.tostring())
        self.assertEqual([], builder.tolist())

    #-----------------------------------------------------------------------#
    # Payload Decoder Tests
    #-----------------------------------------------------------------------#

    def testLittleEndianPayloadDecoder(self):
        ''' Test basic bit message encoding/decoding '''
        decoder = PayloadDecoder(self.little_endian_payload, endian=Endian.Little)
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
        self.assertEqual(self.bitstring, decoder.decode_bits())

    def testBigEndianPayloadDecoder(self):
        ''' Test basic bit message encoding/decoding '''
        decoder = PayloadDecoder(self.big_endian_payload, endian=Endian.Big)
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
        self.assertEqual(self.bitstring, decoder.decode_bits())

    def testPayloadDecoderReset(self):
        ''' Test the payload decoder reset functionality '''
        decoder = PayloadDecoder('\x12\x34')
        self.assertEqual(0x12, decoder.decode_8bit_uint())
        self.assertEqual(0x34, decoder.decode_8bit_uint())
        decoder.reset()   
        self.assertEqual(0x3412, decoder.decode_16bit_uint())

    def testPayloadDecoderRegisterFactory(self):
        ''' Test the payload decoder reset functionality '''
        payload = [1,2,3,4]
        decoder = PayloadDecoder.fromRegisters(payload, endian=Endian.Little)
        encoded = '\x01\x00\x02\x00\x03\x00\x04\x00'
        self.assertEqual(encoded, decoder.decode_string(8))

        decoder = PayloadDecoder.fromRegisters(payload, endian=Endian.Big)
        encoded = '\x00\x01\x00\x02\x00\x03\x00\x04'
        self.assertEqual(encoded, decoder.decode_string(8))

        self.assertRaises(ParameterException, lambda: PayloadDecoder.fromRegisters('abcd'))

    def testPayloadDecoderCoilFactory(self):
        ''' Test the payload decoder reset functionality '''
        payload = [1,0,0,0, 1,0,0,0, 0,0,0,1, 0,0,0,1]
        decoder = PayloadDecoder.fromCoils(payload, endian=Endian.Little)
        encoded = '\x11\x88'
        self.assertEqual(encoded, decoder.decode_string(2))

        decoder = PayloadDecoder.fromCoils(payload, endian=Endian.Big)
        encoded = '\x11\x88'
        self.assertEqual(encoded, decoder.decode_string(2))

        self.assertRaises(ParameterException, lambda: PayloadDecoder.fromCoils('abcd'))


#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
