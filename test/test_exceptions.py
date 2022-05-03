#!/usr/bin/env python3
"""Test exceptions."""
import unittest

from pymodbus.exceptions import (
    ModbusException,
    ConnectionException,
    NotImplementedException,
    ParameterException,
    ModbusIOException,
)


class SimpleExceptionsTest(unittest.TestCase):
    """Unittest for the pymodbus.exceptions module."""

    def setUp(self):
        """Initialize the test environment"""
        self.exceptions = [
            ModbusException("bad base"),
            ModbusIOException("bad register"),
            ParameterException("bad parameter"),
            NotImplementedException("bad function"),
            ConnectionException("bad connection"),
        ]

    def tearDown(self):
        """Clean up the test environment"""

    def test_exceptions(self):
        """Test all module exceptions"""
        for exc in self.exceptions:
            try:
                raise exc
            except ModbusException as exc:
                self.assertTrue("Modbus Error:" in str(exc))
                return
            self.fail("Excepted a ModbusExceptions")


# ---------------------------------------------------------------------------#
#  Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
