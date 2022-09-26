"""Test version."""
import unittest

from pymodbus.version import Version, version


class ModbusVersionTest(unittest.TestCase):
    """Unittest for the pymodbus._version code."""

    def setUp(self):
        """Initialize the test environment"""

    def tearDown(self):
        """Clean up the test environment"""

    def test_version_class(self):
        """Test version class."""
        version = Version("test", 1, 2, 3, "sometag")
        self.assertEqual(version.short(), "1.2.3.sometag")
        self.assertEqual(str(version), "[test, version 1.2.3.sometag]")

    def test_current_version(self):
        """Test current version"""
        self.assertEqual(version.package, "pymodbus")
