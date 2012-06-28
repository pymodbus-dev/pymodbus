#!/usr/bin/env python
import unittest

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

    def testInstallConch(self):
        ''' Test that we can install the conch backend '''
        pass

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
