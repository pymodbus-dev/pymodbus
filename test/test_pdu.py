import unittest
from pymodbus.pdu import *
from pymodbus.mexceptions import *

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
        self.assertEqual(result, '\x01')
        self.assertEqual(self.exception.exception_code, 1)

    def testRequestExceptionFactory(self):
        ''' Test all error methods '''
        request = ModbusRequest()
        request.function_code = 1
        for error in [getattr(ModbusExceptions, i)
            for i in dir(ModbusExceptions) if '__' not in i]:
            result = request.doException(error)
            self.assertEqual(str(result), "Exception Response (129, %d)" % error)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
