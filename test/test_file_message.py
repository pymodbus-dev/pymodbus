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

from .modbus_mocks import MockContext

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
        self.assertEqual(result, b'\x12\x34')

    def testReadFifoQueueRequestDecode(self):
        ''' Test basic bit message encoding/decoding '''
        handle  = ReadFifoQueueRequest(0x0000)
        handle.decode(b'\x12\x34')
        self.assertEqual(handle.address, 0x1234)

    def testReadFifoQueueRequest(self):
        ''' Test basic bit message encoding/decoding '''
        context = MockContext()
        handle  = ReadFifoQueueRequest(0x1234)
        result  = handle.execute(context)
        self.assertTrue(isinstance(result, ReadFifoQueueResponse))

        handle.address = -1
        result  = handle.execute(context)
        self.assertEqual(ModbusExceptions.IllegalValue,
                result.exception_code)

        handle.values = [0x00]*33
        result  = handle.execute(context)
        self.assertEqual(ModbusExceptions.IllegalValue,
                result.exception_code)

    def testReadFifoQueueRequestError(self):
        ''' Test basic bit message encoding/decoding '''
        context = MockContext()
        handle  = ReadFifoQueueRequest(0x1234)
        handle.values = [0x00]*32
        result = handle.execute(context)
        self.assertEqual(result.function_code, 0x98)

    def testReadFifoQueueResponseEncode(self):
        ''' Test that the read fifo queue response can encode '''
        message = b'\x00\n\x00\x08\x00\x01\x00\x02\x00\x03\x00\x04'
        handle  = ReadFifoQueueResponse([1,2,3,4])
        result  = handle.encode()
        self.assertEqual(result, message)

    def testReadFifoQueueResponseDecode(self):
        ''' Test that the read fifo queue response can decode '''
        message = b'\x00\n\x00\x08\x00\x01\x00\x02\x00\x03\x00\x04'
        handle  = ReadFifoQueueResponse([1,2,3,4])
        handle.decode(message)
        self.assertEqual(handle.values, [1,2,3,4])

    def testRtuFrameSize(self):
        ''' Test that the read fifo queue response can decode '''
        message = b'\x00\n\x00\x08\x00\x01\x00\x02\x00\x03\x00\x04'
        result  = ReadFifoQueueResponse.calculateRtuFrameSize(message)
        self.assertEqual(result, 14)

    #-----------------------------------------------------------------------#
    # File Record
    #-----------------------------------------------------------------------#

    def testFileRecordLength(self):
        ''' Test file record length generation '''
        record = FileRecord(file_number=0x01, record_number=0x02,
            record_data=b'\x00\x01\x02\x04')
        self.assertEqual(record.record_length, 0x02)
        self.assertEqual(record.response_length, 0x05)

    def testFileRecordComapre(self):
        ''' Test file record comparison operations '''
        record1 = FileRecord(file_number=0x01, record_number=0x02, record_data=b'\x00\x01\x02\x04')
        record2 = FileRecord(file_number=0x01, record_number=0x02, record_data=b'\x00\x0a\x0e\x04')
        record3 = FileRecord(file_number=0x02, record_number=0x03, record_data=b'\x00\x01\x02\x04')
        record4 = FileRecord(file_number=0x01, record_number=0x02, record_data=b'\x00\x01\x02\x04')
        self.assertTrue(record1 == record4)
        self.assertTrue(record1 != record2)
        self.assertNotEqual(record1, record2)
        self.assertNotEqual(record1, record3)
        self.assertNotEqual(record2, record3)
        self.assertEqual(record1, record4)
        self.assertEqual(str(record1), "FileRecord(file=1, record=2, length=2)")
        self.assertEqual(str(record2), "FileRecord(file=1, record=2, length=2)")
        self.assertEqual(str(record3), "FileRecord(file=2, record=3, length=2)")

    #-----------------------------------------------------------------------#
    # Read File Record Request
    #-----------------------------------------------------------------------#

    def testReadFileRecordRequestEncode(self):
        ''' Test basic bit message encoding/decoding '''
        records = [FileRecord(file_number=0x01, record_number=0x02)]
        handle  = ReadFileRecordRequest(records)
        result  = handle.encode()
        self.assertEqual(result, b'\x07\x06\x00\x01\x00\x02\x00\x00')

    def testReadFileRecordRequestDecode(self):
        ''' Test basic bit message encoding/decoding '''
        record  = FileRecord(file_number=0x04, record_number=0x01, record_length=0x02)
        request = b'\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02'
        handle  = ReadFileRecordRequest()
        handle.decode(request)
        self.assertEqual(handle.records[0], record)

    def testReadFileRecordRequestRtuFrameSize(self):
        ''' Test basic bit message encoding/decoding '''
        request = b'\x00\x00\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02'
        handle  = ReadFileRecordRequest()
        size    = handle.calculateRtuFrameSize(request)
        self.assertEqual(size, 0x0e + 5)

    def testReadFileRecordRequestExecute(self):
        ''' Test basic bit message encoding/decoding '''
        handle  = ReadFileRecordRequest()
        result  = handle.execute(None)
        self.assertTrue(isinstance(result, ReadFileRecordResponse))

    #-----------------------------------------------------------------------#
    # Read File Record Response
    #-----------------------------------------------------------------------#

    def testReadFileRecordResponseEncode(self):
        ''' Test basic bit message encoding/decoding '''
        records = [FileRecord(record_data=b'\x00\x01\x02\x03')]
        handle  = ReadFileRecordResponse(records)
        result  = handle.encode()
        self.assertEqual(result, b'\x06\x06\x02\x00\x01\x02\x03')

    def testReadFileRecordResponseDecode(self):
        ''' Test basic bit message encoding/decoding '''
        record  = FileRecord(file_number=0x00, record_number=0x00,
            record_data=b'\x0d\xfe\x00\x20')
        request = b'\x0c\x05\x06\x0d\xfe\x00\x20\x05\x05\x06\x33\xcd\x00\x40'
        handle  = ReadFileRecordResponse()
        handle.decode(request)
        self.assertEqual(handle.records[0], record)

    def testReadFileRecordResponseRtuFrameSize(self):
        ''' Test basic bit message encoding/decoding '''
        request = b'\x00\x00\x0c\x05\x06\x0d\xfe\x00\x20\x05\x05\x06\x33\xcd\x00\x40'
        handle  = ReadFileRecordResponse()
        size    = handle.calculateRtuFrameSize(request)
        self.assertEqual(size, 0x0c + 5)

    #-----------------------------------------------------------------------#
    # Write File Record Request
    #-----------------------------------------------------------------------#

    def testWriteFileRecordRequestEncode(self):
        ''' Test basic bit message encoding/decoding '''
        records = [FileRecord(file_number=0x01, record_number=0x02, record_data=b'\x00\x01\x02\x03')]
        handle  = WriteFileRecordRequest(records)
        result  = handle.encode()
        self.assertEqual(result, b'\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03')

    def testWriteFileRecordRequestDecode(self):
        ''' Test basic bit message encoding/decoding '''
        record  = FileRecord(file_number=0x04, record_number=0x07,
            record_data=b'\x06\xaf\x04\xbe\x10\x0d')
        request = b'\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d'
        handle  = WriteFileRecordRequest()
        handle.decode(request)
        self.assertEqual(handle.records[0], record)

    def testWriteFileRecordRequestRtuFrameSize(self):
        ''' Test write file record request rtu frame size calculation '''
        request = b'\x00\x00\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d'
        handle  = WriteFileRecordRequest()
        size    = handle.calculateRtuFrameSize(request)
        self.assertEqual(size, 0x0d + 5)

    def testWriteFileRecordRequestExecute(self):
        ''' Test basic bit message encoding/decoding '''
        handle  = WriteFileRecordRequest()
        result  = handle.execute(None)
        self.assertTrue(isinstance(result, WriteFileRecordResponse))

    #-----------------------------------------------------------------------#
    # Write File Record Response
    #-----------------------------------------------------------------------#

    def testWriteFileRecordResponseEncode(self):
        ''' Test basic bit message encoding/decoding '''
        records = [FileRecord(file_number=0x01, record_number=0x02, record_data=b'\x00\x01\x02\x03')]
        handle  = WriteFileRecordResponse(records)
        result  = handle.encode()
        self.assertEqual(result, b'\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03')

    def testWriteFileRecordResponseDecode(self):
        ''' Test basic bit message encoding/decoding '''
        record  = FileRecord(file_number=0x04, record_number=0x07,
            record_data=b'\x06\xaf\x04\xbe\x10\x0d')
        request = b'\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d'
        handle  = WriteFileRecordResponse()
        handle.decode(request)
        self.assertEqual(handle.records[0], record)

    def testWriteFileRecordResponseRtuFrameSize(self):
        ''' Test write file record response rtu frame size calculation '''
        request = b'\x00\x00\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d'
        handle  = WriteFileRecordResponse()
        size    = handle.calculateRtuFrameSize(request)
        self.assertEqual(size, 0x0d + 5)


#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
