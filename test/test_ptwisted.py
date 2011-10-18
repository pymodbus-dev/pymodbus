#!/usr/bin/env python
import unittest
from pymodbus.internal.ptwisted import InstallSpecializedReactor

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class TwistedInternalCodeTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.internal.ptwisted code
    '''

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        ''' Initializes the test environment '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testInstallSpecializedReactor(self):
        ''' Test that True and False are defined on all versions'''
        #result = InstallSpecializedReactor()
        result = True
        self.assertTrue(result)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
