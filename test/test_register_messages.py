'''
Register Message Test Fixture
--------------------------------
This fixture tests the functionality of all the 
register based request/response messages:

* Read/Write Input Registers
* Read Holding Registers
'''
import unittest
from pymodbus.register_read_message import *
from pymodbus.register_read_message import ReadRegistersRequestBase
from pymodbus.register_read_message import ReadRegistersResponseBase
from pymodbus.register_write_message import *
from pymodbus.exceptions import *
from pymodbus.pdu import ModbusExceptions

#---------------------------------------------------------------------------#
# Mocks
#---------------------------------------------------------------------------#
class Context(object):
    def validate(self, a,b,c):
        return False

    def getValues(self, a, b, count):
        return [1] * count
#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class RegisterMessagesTest(unittest.TestCase):

    def setUp(self):
        '''
        Initializes the test environment and builds request/result
        encoding pairs
        '''
        self.value  = 0xabcd
        self.values = [0xa, 0xb, 0xc]
        self.rread = {
            ReadRegistersRequestBase(1, 5)                  :'\x00\x01\x00\x05',
            ReadRegistersResponseBase(self.values)          :'\x06\x00\x0a\x00\x0b\x00\x0c',
            ReadHoldingRegistersRequest(1, 5)               :'\x00\x01\x00\x05',
            ReadHoldingRegistersResponse(self.values)       :'\x06\x00\x0a\x00\x0b\x00\x0c',
            ReadInputRegistersRequest(1,5)                  :'\x00\x01\x00\x05',
            ReadInputRegistersResponse(self.values)         :'\x06\x00\x0a\x00\x0b\x00\x0c',
            ReadWriteMultipleRegistersRequest(1,5,1,5)      :'\x00\x01\x00\x05\x00\x01\x00'
                                                             '\x05\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
            ReadWriteMultipleRegistersResponse(self.values) :'\x06\x00\x0a\x00\x0b\x00\x0c',
        }

        self.rwrite = {
            WriteSingleRegisterRequest(1, self.value)       : '\x00\x01\xab\xcd',
            WriteSingleRegisterResponse(1, self.value)      : '\x00\x01\xab\xcd',
            WriteMultipleRegistersRequest(1, 5)             : '\x00\x01\x00\x05\x0a\x00\x00\x00\x00\x00\x00'
                                                              '\x00\x00\x00\x00',
            WriteMultipleRegistersResponse(1, 5)            : '\x00\x01\x00\x05',
        }

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.rread
        del self.rwrite

    def testRegisterReadRequests(self):
        ''' Test register read request encoding '''
        for rqst, rsp in self.rread.iteritems():
            self.assertEqual(rqst.encode(), rsp)

    def testRegisterReadRequestsCountErrors(self):
        '''
        This tests that the register request messages
        will break on counts that are out of range
        '''
        requests = [
            ReadHoldingRegistersRequest(1, 0x800),
            ReadInputRegistersRequest(1,0x800),
            ReadWriteMultipleRegistersRequest(1,0x800,1,5),
            ReadWriteMultipleRegistersRequest(1,5,1,0x800),
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
        context = Context()
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

    def testRegisterWriteRequests(self):
        ''' Test register write request encoding '''
        for rqst, rsp in self.rwrite.iteritems():
            self.assertEqual(rqst.encode(), rsp)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
