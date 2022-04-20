#!/usr/bin/env python3
""" Test ptwisted. """
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

    def test_install_conch(self):
        ''' Test that we can install the conch backend '''

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
