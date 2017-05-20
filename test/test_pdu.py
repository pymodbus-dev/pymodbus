#!/usr/bin/env python
import unittest
from pymodbus.pdu import *
from pymodbus.exceptions import *
from pymodbus.compat import iteritems

class SimplePduTest(unittest.TestCase):
    '''
    This is the unittest for the pymod.pdu module
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        self.badRequests = (
        #       ModbusPDU(),
                ModbusRequest(),
                ModbusResponse(),
        )
        self.illegal = IllegalFunctionRequest(1)
        self.exception = ExceptionResponse(1,1)

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.badRequests
        del self.illegal
        del self.exception

    def testNotImpelmented(self):
        ''' Test a base classes for not implemented funtions '''
        for r in self.badRequests:
            self.assertRaises(NotImplementedException, r.encode)

        for r in self.badRequests:
            self.assertRaises(NotImplementedException, r.decode, None)

    def testErrorMethods(self):
        ''' Test all error methods '''
        self.illegal.decode("12345")
        self.illegal.execute(None)

        result = self.exception.encode()
        self.exception.decode(result)
        self.assertEqual(result, b'\x01')
        self.assertEqual(self.exception.exception_code, 1)

    def testRequestExceptionFactory(self):
        ''' Test all error methods '''
        request = ModbusRequest()
        request.function_code = 1
        errors = dict((ModbusExceptions.decode(c), c) for c in range(1,20))
        for error, code in iteritems(errors):
            result = request.doException(code)
            self.assertEqual(str(result), "Exception Response(129, 1, %s)" % error)

    def testCalculateRtuFrameSize(self):
        ''' Test the calculation of Modbus/RTU frame sizes '''
        self.assertRaises(NotImplementedException,
                          ModbusRequest.calculateRtuFrameSize, b'')
        ModbusRequest._rtu_frame_size = 5
        self.assertEqual(ModbusRequest.calculateRtuFrameSize(b''), 5)
        del ModbusRequest._rtu_frame_size

        ModbusRequest._rtu_byte_count_pos = 2
        self.assertEqual(ModbusRequest.calculateRtuFrameSize(
            b'\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6'), 0x05 + 5)
        del ModbusRequest._rtu_byte_count_pos
        
        self.assertRaises(NotImplementedException,
                          ModbusResponse.calculateRtuFrameSize, b'')
        ModbusResponse._rtu_frame_size = 12
        self.assertEqual(ModbusResponse.calculateRtuFrameSize(b''), 12)
        del ModbusResponse._rtu_frame_size
        ModbusResponse._rtu_byte_count_pos = 2
        self.assertEqual(ModbusResponse.calculateRtuFrameSize(
            b'\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6'), 0x05 + 5)
        del ModbusResponse._rtu_byte_count_pos
        
        
#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
