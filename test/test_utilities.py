#!/usr/bin/env python
import unittest
import struct
from pymodbus.utilities import pack_bitstring, unpack_bitstring
from pymodbus.utilities import checkCRC, checkLRC
from pymodbus.utilities import dict_property, default

_test_master = {4 : 'd'}
class DictPropertyTester(object):
    def __init__(self):
        self.test   = {1 : 'a'}
        self._test  = {2 : 'b'}
        self.__test = {3 : 'c'}

    l1 = dict_property(lambda s: s.test, 1)
    l2 = dict_property(lambda s: s._test, 2)
    l3 = dict_property(lambda s: s.__test, 3)
    s1 = dict_property('test', 1)
    s2 = dict_property('_test', 2)
    g1 = dict_property(_test_master, 4)


class SimpleUtilityTest(unittest.TestCase):
    '''
    This is the unittest for the pymod.utilities module
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        self.data = struct.pack('>HHHH', 0x1234, 0x2345, 0x3456, 0x4567)
        self.string = b"test the computation"
        self.bits = [True, False, True, False, True, False, True, False]

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.bits
        del self.string

    def testDictProperty(self):
        ''' Test all string <=> bit packing functions '''
        d = DictPropertyTester()
        self.assertEqual(d.l1, 'a')
        self.assertEqual(d.l2, 'b')
        self.assertEqual(d.l3, 'c')
        self.assertEqual(d.s1, 'a')
        self.assertEqual(d.s2, 'b')
        self.assertEqual(d.g1, 'd')

        for store in 'l1 l2 l3 s1 s2 g1'.split(' '):
            setattr(d, store, 'x')

        self.assertEqual(d.l1, 'x')
        self.assertEqual(d.l2, 'x')
        self.assertEqual(d.l3, 'x')
        self.assertEqual(d.s1, 'x')
        self.assertEqual(d.s2, 'x')
        self.assertEqual(d.g1, 'x')

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
        self.assertEqual(unpack_bitstring(b'\x55'), self.bits)
        self.assertEqual(pack_bitstring(self.bits), b'\x55')

    def testLongitudinalRedundancyCheck(self):
        ''' Test the longitudinal redundancy check code '''
        self.assertTrue(checkLRC(self.data, 0x1c))
        self.assertTrue(checkLRC(self.string, 0x0c))

    def testCyclicRedundancyCheck(self):
        ''' Test the cyclic redundancy check code '''
        self.assertTrue(checkCRC(self.data, 0xe2db))
        self.assertTrue(checkCRC(self.string, 0x889e))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
