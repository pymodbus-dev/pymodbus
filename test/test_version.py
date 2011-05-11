#!/usr/bin/env python
import unittest
from pymodbus.version import Version

class ModbusVersionTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus._version code
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testVersionClass(self):
        version = Version('test', 1,2,3)
        self.assertEqual(version.short(), '1.2.3')
        self.assertEqual(str(version), '[test, version 1.2.3]')

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
