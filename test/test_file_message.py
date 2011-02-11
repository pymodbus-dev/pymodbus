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
from pymodbus.file_message import *
from pymodbus.exceptions import *
from pymodbus.pdu import ModbusExceptions

from modbus_mocks import MockContext

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

    #-----------------------------------------------------------------------#
    # Read Fifo Queue
    #-----------------------------------------------------------------------#

    def testReadFifoQueueRequestEncode(self):
        ''' Test basic bit message encoding/decoding '''
        handle  = ReadFifoQueueRequest(0x1234)
        result  = handle.encode()
        self.assertEqual(result, '\x12\x34')

    def testReadFifoQueueRequestDecode(self):
        ''' Test basic bit message encoding/decoding '''
        handle  = ReadFifoQueueRequest(0x0000)
        handle.decode('\x12\x34')
        self.assertEqual(handle.address, 0x1234)

    def testReadFifoQueueRequest(self):
        ''' Test basic bit message encoding/decoding '''
        context = MockContext()
        handle  = ReadFifoQueueRequest(0x1234)
        result  = handle.execute(context)
        self.assertTrue(isinstance(result, ReadFifoQueueResponse))

    def testReadFifoQueueRequestError(self):
        ''' Test basic bit message encoding/decoding '''
        context = MockContext()
        handle  = ReadFifoQueueRequest(0x1234)
        handle.values = [0x00]*32
        result = handle.execute(context)
        self.assertEqual(result.function_code, 0x98)

    def testReadFifoQueueResponseEncode(self):
        ''' Test that the read fifo queue response can encode '''
        message = '\x00\n\x00\x08\x00\x01\x00\x02\x00\x03\x00\x04'
        handle  = ReadFifoQueueResponse([1,2,3,4])
        result  = handle.encode()
        self.assertEqual(result, message)

    def testReadFifoQueueResponseDecode(self):
        ''' Test that the read fifo queue response can decode '''
        message = '\x00\n\x00\x08\x00\x01\x00\x02\x00\x03\x00\x04'
        handle  = ReadFifoQueueResponse([1,2,3,4])
        handle.decode(message)
        self.assertEqual(handle.values, [1,2,3,4])

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
