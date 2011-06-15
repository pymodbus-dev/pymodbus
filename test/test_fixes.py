#!/usr/bin/env python
import unittest

class ModbusFixesTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus._version code
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testTrueFalseDefined(self):
        ''' Test that True and False are defined on all versions'''
        try:
            True,False
        except NameError:
            import pymodbus
            self.assertEqual(True, 1)
            self.assertEqual(False, 1)

    def testNullLoggerAttached(self):
        ''' Test that the null logger is attached'''
        import logging
        if len(logging._handlers) == 0:
          import pymodbus
          self.assertEqual(logging._handlers, 1)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
