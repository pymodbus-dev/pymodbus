#!/usr/bin/env python
import unittest
from pymodbus.register_read_message import *
from pymodbus.register_read_message import ReadRegistersRequestBase
from pymodbus.register_read_message import ReadRegistersResponseBase
from pymodbus.exceptions import *
from pymodbus.pdu import ModbusExceptions
from pymodbus.compat import iteritems, iterkeys, get_next

from .modbus_mocks import MockContext, FakeList

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class ReadRegisterMessagesTest(unittest.TestCase):
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
        arguments = {
            'read_address':  1, 'read_count': 5,
            'write_address': 1, 'write_registers': [0x00]*5,
        }
        self.value  = 0xabcd
        self.values = [0xa, 0xb, 0xc]
        self.request_read  = {
            ReadRegistersRequestBase(1, 5)                  :b'\x00\x01\x00\x05',
            ReadHoldingRegistersRequest(1, 5)               :b'\x00\x01\x00\x05',
            ReadInputRegistersRequest(1,5)                  :b'\x00\x01\x00\x05',
            ReadWriteMultipleRegistersRequest(**arguments)  :b'\x00\x01\x00\x05\x00\x01\x00'
                                                             b'\x05\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        }
        self.response_read  = {
            ReadRegistersResponseBase(self.values)          :b'\x06\x00\x0a\x00\x0b\x00\x0c',
            ReadHoldingRegistersResponse(self.values)       :b'\x06\x00\x0a\x00\x0b\x00\x0c',
            ReadInputRegistersResponse(self.values)         :b'\x06\x00\x0a\x00\x0b\x00\x0c',
            ReadWriteMultipleRegistersResponse(self.values) :b'\x06\x00\x0a\x00\x0b\x00\x0c',
        }

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.request_read
        del self.response_read

    def testReadRegisterResponseBase(self):
        response = ReadRegistersResponseBase(list(range(10)))
        for index in range(10):
            self.assertEqual(response.getRegister(index), index)

    def testRegisterReadRequests(self):
        for request, response in iteritems(self.request_read):
            self.assertEqual(request.encode(), response)

    def testRegisterReadResponses(self):
        for request, response in iteritems(self.response_read):
            self.assertEqual(request.encode(), response)

    def testRegisterReadResponseDecode(self):
        registers = [
            [0x0a,0x0b,0x0c],
            [0x0a,0x0b,0x0c],
            [0x0a,0x0b,0x0c],
            [0x0a,0x0b,0x0c, 0x0a,0x0b,0x0c],
        ]
        values = sorted(self.response_read.items(), key=lambda x: str(x))
        for packet, register in zip(values, registers):
            request, response = packet
            request.decode(response)
            self.assertEqual(request.registers, register)

    def testRegisterReadRequestsCountErrors(self):
        '''
        This tests that the register request messages
        will break on counts that are out of range
        '''
        mock = FakeList(0x800)
        requests = [
            ReadHoldingRegistersRequest(1, 0x800),
            ReadInputRegistersRequest(1,0x800),
            ReadWriteMultipleRegistersRequest(read_address=1,
                read_count=0x800, write_address=1, write_registers=5),
            ReadWriteMultipleRegistersRequest(read_address=1,
                read_count=5, write_address=1, write_registers=mock),
        ]
        for request in requests:
            result = request.execute(None)
            self.assertEqual(ModbusExceptions.IllegalValue,
                result.exception_code)

    def testRegisterReadRequestsValidateErrors(self):
        '''
        This tests that the register request messages
        will break on counts that are out of range
        '''
        context = MockContext()
        requests = [
            ReadHoldingRegistersRequest(-1, 5),
            ReadInputRegistersRequest(-1,5),
            #ReadWriteMultipleRegistersRequest(-1,5,1,5),
            #ReadWriteMultipleRegistersRequest(1,5,-1,5),
        ]
        for request in requests:
            result = request.execute(context)
            self.assertEqual(ModbusExceptions.IllegalAddress,
                result.exception_code)

    def testRegisterReadRequestsExecute(self):
        '''
        This tests that the register request messages
        will break on counts that are out of range
        '''
        context = MockContext(True)
        requests = [
            ReadHoldingRegistersRequest(-1, 5),
            ReadInputRegistersRequest(-1,5),
        ]
        for request in requests:
            response = request.execute(context)
            self.assertEqual(request.function_code, response.function_code)

    def testReadWriteMultipleRegistersRequest(self):
        context = MockContext(True)
        request = ReadWriteMultipleRegistersRequest(read_address=1,
            read_count=10, write_address=1, write_registers=[0x00])
        response = request.execute(context)
        self.assertEqual(request.function_code, response.function_code)

    def testReadWriteMultipleRegistersValidate(self):
        context = MockContext()
        context.validate = lambda f,a,c: a == 1
        request = ReadWriteMultipleRegistersRequest(read_address=1,
            read_count=10, write_address=2, write_registers=[0x00])
        response = request.execute(context)
        self.assertEqual(response.exception_code, ModbusExceptions.IllegalAddress)

        context.validate = lambda f,a,c: a == 2
        response = request.execute(context)
        self.assertEqual(response.exception_code, ModbusExceptions.IllegalAddress)

        request.write_byte_count = 0x100
        response = request.execute(context)
        self.assertEqual(response.exception_code, ModbusExceptions.IllegalValue)

    def testReadWriteMultipleRegistersRequestDecode(self):
        request, response = get_next((k,v) for k,v in self.request_read.items()
            if getattr(k, 'function_code', 0) == 23)
        request.decode(response)
        self.assertEqual(request.read_address, 0x01)
        self.assertEqual(request.write_address, 0x01)
        self.assertEqual(request.read_count, 0x05)
        self.assertEqual(request.write_count, 0x05)
        self.assertEqual(request.write_byte_count, 0x0a)
        self.assertEqual(request.write_registers, [0x00]*5)

    def testSerializingToString(self):
        for request in iterkeys(self.request_read):
            self.assertTrue(str(request) != None)
        for request in iterkeys(self.response_read):
            self.assertTrue(str(request) != None)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
