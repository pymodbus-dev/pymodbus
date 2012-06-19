#!/usr/bin/env python
import unittest

class ModbusFixesTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus._version code
    '''

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
        logger = logging.getLogger('pymodbus')
        self.assertEqual(len(logger.handlers), 1)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
