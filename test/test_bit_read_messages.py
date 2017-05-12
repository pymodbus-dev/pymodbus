#!/usr/bin/env python
'''
Bit Message Test Fixture
--------------------------------
This fixture tests the functionality of all the 
bit based request/response messages:

* Read/Write Discretes
* Read Coils
'''
import unittest, struct
from pymodbus.bit_read_message import *
from pymodbus.bit_read_message import ReadBitsRequestBase
from pymodbus.bit_read_message import ReadBitsResponseBase
from pymodbus.exceptions import *
from pymodbus.pdu import ModbusExceptions
from pymodbus.compat import iteritems

from .modbus_mocks import MockContext

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class ModbusBitMessageTests(unittest.TestCase):

    def testReadBitBaseClassMethods(self):
        ''' Test basic bit message encoding/decoding '''
        handle = ReadBitsRequestBase(1, 1)
        msg    = "ReadBitRequest(1,1)"
        self.assertEqual(msg, str(handle))
        handle = ReadBitsResponseBase([1,1])
        msg    = "ReadBitResponse(2)"
        self.assertEqual(msg, str(handle))

    def testBitReadBaseRequestEncoding(self):
        ''' Test basic bit message encoding/decoding '''
        for i in range(20):
            handle = ReadBitsRequestBase(i, i)
            result = struct.pack('>HH',i, i)
            self.assertEqual(handle.encode(), result)
            handle.decode(result)
            self.assertEqual((handle.address, handle.count), (i,i))

    def testBitReadBaseResponseEncoding(self):
        ''' Test basic bit message encoding/decoding '''
        for i in range(20):
            input  = [True] * i
            handle = ReadBitsResponseBase(input)
            result = handle.encode()
            handle.decode(result)
            self.assertEqual(handle.bits[:i], input)

    def testBitReadBaseResponseHelperMethods(self):
        ''' Test the extra methods on a ReadBitsResponseBase '''
        input  = [False] * 8
        handle = ReadBitsResponseBase(input)
        for i in [1,3,5]: handle.setBit(i, True)
        for i in [1,3,5]: handle.resetBit(i)
        for i in range(8):
            self.assertEqual(handle.getBit(i), False)

    def testBitReadBaseRequests(self):
        ''' Test bit read request encoding '''
        messages = {
            ReadBitsRequestBase(12, 14)        : b'\x00\x0c\x00\x0e',
            ReadBitsResponseBase([1,0,1,1,0])  : b'\x01\x0d',
        }
        for request, expected in iteritems(messages):
            self.assertEqual(request.encode(), expected)

    def testBitReadMessageExecuteValueErrors(self):
        ''' Test bit read request encoding '''
        context = MockContext()
        requests = [
            ReadCoilsRequest(1,0x800),
            ReadDiscreteInputsRequest(1,0x800),
        ]
        for request in requests:
            result = request.execute(context)
            self.assertEqual(ModbusExceptions.IllegalValue,
                result.exception_code)

    def testBitReadMessageExecuteAddressErrors(self):
        ''' Test bit read request encoding '''
        context = MockContext()
        requests = [
            ReadCoilsRequest(1,5),
            ReadDiscreteInputsRequest(1,5),
        ]
        for request in requests:
            result = request.execute(context)
            self.assertEqual(ModbusExceptions.IllegalAddress, result.exception_code)

    def testBitReadMessageExecuteSuccess(self):
        ''' Test bit read request encoding '''
        context = MockContext()
        context.validate = lambda a,b,c: True
        requests = [
            ReadCoilsRequest(1,5),
            ReadDiscreteInputsRequest(1,5),
        ]
        for request in requests:
            result = request.execute(context)
            self.assertEqual(result.bits, [True] * 5)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
