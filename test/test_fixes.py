#!/usr/bin/env python3
"""Test fixes."""
import logging
import unittest


class ModbusFixesTest(unittest.TestCase):
    """Unittest for the pymodbus._version code."""

    def test_true_false_defined(self):
        """Test that True and False are defined on all versions"""
        try:
            True, False
        except NameError:
            self.assertEqual(True, 1)
            self.assertEqual(False, 1)

    def test_null_logger_attached(self):
        """Test that the null logger is attached"""
        logger = logging.getLogger("pymodbus")
        self.assertEqual(len(logger.handlers), 1)


# ---------------------------------------------------------------------------#
#  Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
