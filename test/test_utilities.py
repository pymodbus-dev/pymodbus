"""Test utilities."""
import struct
import unittest

from pymodbus.utilities import (
    checkCRC,
    checkLRC,
    default,
    dict_property,
    pack_bitstring,
    unpack_bitstring,
)


_test_master = {4: "d"}


class DictPropertyTester:  # pylint: disable=too-few-public-methods
    """Dictionary property test."""

    def __init__(self):
        """Initialize."""
        self.test = {1: "a"}
        self._test = {2: "b"}
        self.__test = {3: "c"}  # pylint: disable=unused-private-member

    l_1 = dict_property(lambda s: s.test, 1)
    l_2 = dict_property(lambda s: s._test, 2)  # pylint: disable=protected-access
    l_3 = dict_property(lambda s: s.__test, 3)  # pylint: disable=protected-access
    s_1 = dict_property("test", 1)
    s_2 = dict_property("_test", 2)
    g_1 = dict_property(_test_master, 4)


class SimpleUtilityTest(unittest.TestCase):
    """Unittest for the pymod.utilities module."""

    def setUp(self):
        """Initialize the test environment"""
        self.data = struct.pack(">HHHH", 0x1234, 0x2345, 0x3456, 0x4567)
        self.string = b"test the computation"
        self.bits = [True, False, True, False, True, False, True, False]

    def tearDown(self):
        """Clean up the test environment"""
        del self.bits
        del self.string

    def test_dict_property(self):
        """Test all string <=> bit packing functions"""
        result = DictPropertyTester()
        self.assertEqual(result.l_1, "a")
        self.assertEqual(result.l_2, "b")
        self.assertEqual(result.l_3, "c")
        self.assertEqual(result.s_1, "a")
        self.assertEqual(result.s_2, "b")
        self.assertEqual(result.g_1, "d")

        for store in "l_1 l_2 l_3 s_1 s_2 g_1".split(" "):
            setattr(result, store, "x")

        self.assertEqual(result.l_1, "x")
        self.assertEqual(result.l_2, "x")
        self.assertEqual(result.l_3, "x")
        self.assertEqual(result.s_1, "x")
        self.assertEqual(result.s_2, "x")
        self.assertEqual(result.g_1, "x")

    def test_default_value(self):
        """Test all string <=> bit packing functions"""
        self.assertEqual(default(1), 0)
        self.assertEqual(default(1.1), 0.0)
        self.assertEqual(default(1 + 1j), 0j)
        self.assertEqual(default("string"), "")
        self.assertEqual(default([1, 2, 3]), [])
        self.assertEqual(default({1: 1}), {})
        self.assertEqual(default(True), False)

    def test_bit_packing(self):
        """Test all string <=> bit packing functions"""
        self.assertEqual(unpack_bitstring(b"\x55"), self.bits)
        self.assertEqual(pack_bitstring(self.bits), b"\x55")

    def test_longitudinal_redundancycheck(self):
        """Test the longitudinal redundancy check code"""
        self.assertTrue(checkLRC(self.data, 0x1C))
        self.assertTrue(checkLRC(self.string, 0x0C))

    def test_cyclic_redundancy_check(self):
        """Test the cyclic redundancy check code"""
        self.assertTrue(checkCRC(self.data, 0xE2DB))
        self.assertTrue(checkCRC(self.string, 0x889E))
