import unittest
from pymodbus.utilities import *

class SimpleUtilityTest(unittest.TestCase):
    '''
    This is the unittest for the pymod.utilities module
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        self.string = "test the computation"
        self.bits = [True, False, True, False, True, False, True, False]

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.bits
        del self.string

    def testBitPacking(self):
        ''' Test all string <=> bit packing functions '''
        self.assertEqual(unpackBitsFromString('\01U'), (self.bits,1))
        self.assertEqual(packBitsToString(self.bits), 'U')

    def testDataErrorChecking(self):
        ''' Test all error detection computations '''
        self.assertTrue(checkCRC(self.string, 0x9e88))
        self.assertTrue(checkLRC(self.string, 2))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
