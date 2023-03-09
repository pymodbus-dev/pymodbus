"""Test version."""
import unittest

from pymodbus import __version__ as pymodbus_version
from pymodbus import __version_full__ as pymodbus_version_full
from pymodbus.version import Version, version


class ModbusVersionTest(unittest.TestCase):
    """Unittest for the pymodbus._version code."""

    def setUp(self):
        """Initialize the test environment"""

    def tearDown(self):
        """Clean up the test environment"""

    def test_version_class(self):
        """Test version class."""
        test_version = Version("test", 1, 2, 3, "sometag")
        self.assertEqual(test_version.short(), "1.2.3.sometag")
        self.assertEqual(str(test_version), "[test, version 1.2.3.sometag]")
        self.assertEqual(test_version.package, "test")

        self.assertEqual(pymodbus_version, version.short())
        self.assertEqual(pymodbus_version_full, str(version))
        self.assertEqual(version.package, "pymodbus")
