import unittest
import struct
from pymodbus.utilities import *

class SimpleUtilityTest(unittest.TestCase):
    '''
    This is the unittest for the pymod.utilities module
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        self.data = struct.pack('>HHHH', 0x1234, 0x2345, 0x3456, 0x4567)
        self.string = "test the computation"
        self.bits = [True, False, True, False, True, False, True, False]

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.bits
        del self.string

    def testDefaultValue(self):
        ''' Test all string <=> bit packing functions '''
        self.assertEqual(default(1), 0)
        self.assertEqual(default(1.1), 0.0)
        self.assertEqual(default(1+1j), 0j)
        self.assertEqual(default('string'), '')
        self.assertEqual(default([1,2,3]), [])
        self.assertEqual(default({1:1}), {})
        self.assertEqual(default(True), False)

    def testBitPacking(self):
        ''' Test all string <=> bit packing functions '''
        self.assertEqual(unpackBitsFromString('\01U'), (self.bits,1))
        self.assertEqual(packBitsToString(self.bits), 'U')

    def testLongitudinalRedundancyCheck(self):
        ''' Test the longitudinal redundancy check code '''
        self.assertTrue(checkLRC(self.data, 0x1c))
        self.assertTrue(checkLRC(self.string, 0x0c))

    def testCyclicRedundancyCheck(self):
        ''' Test the cyclic redundancy check code '''
        self.assertTrue(checkCRC(self.data, 0xdbe2))
        self.assertTrue(checkCRC(self.string, 0x9e88))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
