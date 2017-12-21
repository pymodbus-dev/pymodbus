#!/usr/bin/env python
import unittest
from pymodbus.datastore.context import ModbusSlaveContext
from pymodbus.datastore.store import ModbusSequentialDataBlock
from base_context import ContextRunner

class MemorySlaveContextTest(ContextRunner, unittest.TestCase):
    """
    These are the integration tests for using the in memory
    slave context.
    """

    def setUp(self):
        """ Initializes the test environment """
        self.context = ModbusSlaveContext(**{
            'di' : ModbusSequentialDataBlock(0, [0]*100),
            'co' : ModbusSequentialDataBlock(0, [0]*100),
            'ir' : ModbusSequentialDataBlock(0, [0]*100),
            'hr' : ModbusSequentialDataBlock(0, [0]*100)})
        self.initialize()

    def tearDown(self):
        """ Cleans up the test environment """
        self.shutdown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
