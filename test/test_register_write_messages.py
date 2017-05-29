#!/usr/bin/env python
import unittest
from pymodbus.register_write_message import *
from pymodbus.exceptions import ParameterException
from pymodbus.pdu import ModbusExceptions
from pymodbus.compat import iteritems, iterkeys
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import Endian

from .modbus_mocks import MockContext

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class WriteRegisterMessagesTest(unittest.TestCase):
    '''
    Register Message Test Fixture
    --------------------------------
    This fixture tests the functionality of all the 
    register based request/response messages:
    
    * Read/Write Input Registers
    * Read Holding Registers
    '''

    def setUp(self):
        '''
        Initializes the test environment and builds request/result
        encoding pairs
        '''
        self.value  = 0xabcd
        self.values = [0xa, 0xb, 0xc]
        builder = BinaryPayloadBuilder(endian=Endian.Big)
        builder.add_16bit_uint(0x1234)
        self.payload = builder.build()
        self.write  = {
            WriteSingleRegisterRequest(1, self.value)       : b'\x00\x01\xab\xcd',
            WriteSingleRegisterResponse(1, self.value)      : b'\x00\x01\xab\xcd',
            WriteMultipleRegistersRequest(1, self.values)   : b'\x00\x01\x00\x03\x06\x00\n\x00\x0b\x00\x0c',
            WriteMultipleRegistersResponse(1, 5)            : b'\x00\x01\x00\x05',

            WriteSingleRegisterRequest(1, self.payload[0], skip_encode=True): b'\x00\x01\x12\x34',
            WriteMultipleRegistersRequest(1, self.payload, skip_encode=True): b'\x00\x01\x00\x01\x02\x12\x34',
        }

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.write

    def testRegisterWriteRequestsEncode(self):
        for request, response in iteritems(self.write):
            self.assertEqual(request.encode(), response)

    def testRegisterWriteRequestsDecode(self):
        addresses = [1,1,1,1]
        values = sorted(self.write.items(), key=lambda x: str(x))
        for packet, address in zip(values, addresses):
            request, response = packet
            request.decode(response)
            self.assertEqual(request.address, address)

    def testInvalidWriteMultipleRegistersRequest(self):
        request = WriteMultipleRegistersRequest(0, None)
        self.assertEqual(request.values, [])

    def testSerializingToString(self):
        for request in iterkeys(self.write):
            self.assertTrue(str(request) != None)

    def testWriteSingleRegisterRequest(self):
        context = MockContext()
        request = WriteSingleRegisterRequest(0x00, 0xf0000)
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        request.value = 0x00ff
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalAddress)

        context.valid = True
        result = request.execute(context)
        self.assertEqual(result.function_code, request.function_code)

    def testWriteMultipleRegisterRequest(self):
        context = MockContext()
        request = WriteMultipleRegistersRequest(0x00, [0x00]*10)
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalAddress)

        request.count = 0x05 # bytecode != code * 2
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        request.count = 0x800 # outside of range
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        context.valid = True
        request = WriteMultipleRegistersRequest(0x00, [0x00]*10)
        result = request.execute(context)
        self.assertEqual(result.function_code, request.function_code)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
