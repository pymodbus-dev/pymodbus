#!/usr/bin/env python
import unittest
from pymodbus.exceptions import *

class SimpleExceptionsTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.exceptions module
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        self.exceptions = [
                ModbusException("bad base"),
                ModbusIOException("bad register"),
                ParameterException("bad paramater"),
                NotImplementedException("bad function"),
                ConnectionException("bad connection"),
        ]

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testExceptions(self):
        ''' Test all module exceptions '''
        for ex in self.exceptions:
            try:
                raise ex
            except ModbusException as ex:
                self.assertTrue("Modbus Error:" in str(ex))
                pass
            else: self.fail("Excepted a ModbusExceptions")

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
