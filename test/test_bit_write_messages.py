#!/usr/bin/env python
'''
Bit Message Test Fixture
--------------------------------
This fixture tests the functionality of all the 
bit based request/response messages:

* Read/Write Discretes
* Read Coils
'''
import unittest
from pymodbus.bit_write_message import *
from pymodbus.exceptions import *
from pymodbus.pdu import ModbusExceptions
from pymodbus.compat import iteritems

from .modbus_mocks import MockContext, FakeList

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class ModbusBitMessageTests(unittest.TestCase):

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        '''
        Initializes the test environment and builds request/result
        encoding pairs
        '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testBitWriteBaseRequests(self):
        messages = {
            WriteSingleCoilRequest(1, 0xabcd)      : b'\x00\x01\xff\x00',
            WriteSingleCoilResponse(1, 0xabcd)     : b'\x00\x01\xff\x00',
            WriteMultipleCoilsRequest(1, [True]*5) : b'\x00\x01\x00\x05\x01\x1f',
            WriteMultipleCoilsResponse(1, 5)       : b'\x00\x01\x00\x05',
        }
        for request, expected in iteritems(messages):
            self.assertEqual(request.encode(), expected)

    def testBitWriteMessageGetResponsePDU(self):
        requests = {
            WriteSingleCoilRequest(1, 0xabcd): 5
        }
        for request, expected in iteritems(requests):
            pdu_len = request.get_response_pdu_size()
            self.assertEqual(pdu_len, expected)

    def testWriteMultipleCoilsRequest(self):
        request = WriteMultipleCoilsRequest(1, [True]*5)
        request.decode(b'\x00\x01\x00\x05\x01\x1f')
        self.assertEqual(request.byte_count, 1)
        self.assertEqual(request.address, 1)
        self.assertEqual(request.values, [True]*5)
        self.assertEqual(request.get_response_pdu_size(), 5)


    def testInvalidWriteMultipleCoilsRequest(self):
        request = WriteMultipleCoilsRequest(1, None)
        self.assertEqual(request.values, [])

    def testWriteSingleCoilRequestEncode(self):
        request = WriteSingleCoilRequest(1, False)
        self.assertEqual(request.encode(), b'\x00\x01\x00\x00')

    def testWriteSingleCoilExecute(self):
        context = MockContext(False, default=True)
        request = WriteSingleCoilRequest(2, True)
        result  = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalAddress)

        context.valid = True
        result = request.execute(context)
        self.assertEqual(result.encode(), b'\x00\x02\xff\x00')

        context = MockContext(True, default=False)
        request = WriteSingleCoilRequest(2, False)
        result = request.execute(context)
        self.assertEqual(result.encode(), b'\x00\x02\x00\x00')

    def testWriteMultipleCoilsExecute(self):
        context = MockContext(False)
        # too many values
        request = WriteMultipleCoilsRequest(2, FakeList(0x123456))
        result  = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        # bad byte count
        request = WriteMultipleCoilsRequest(2, [0x00]*4)
        request.byte_count = 0x00
        result  = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        # does not validate
        context.valid = False
        request = WriteMultipleCoilsRequest(2, [0x00]*4)
        result  = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalAddress)

        # validated request
        context.valid = True
        result  = request.execute(context)
        self.assertEqual(result.encode(), b'\x00\x02\x00\x04')

    def testWriteMultipleCoilsResponse(self):
        response = WriteMultipleCoilsResponse()
        response.decode(b'\x00\x80\x00\x08')
        self.assertEqual(response.address, 0x80)
        self.assertEqual(response.count, 0x08)

    def testSerializingToString(self):
        requests = [
            WriteSingleCoilRequest(1, 0xabcd),
            WriteSingleCoilResponse(1, 0xabcd),
            WriteMultipleCoilsRequest(1, [True]*5),
            WriteMultipleCoilsResponse(1, 5),
        ]
        for request in requests:
            self.assertTrue(str(request) != None)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
