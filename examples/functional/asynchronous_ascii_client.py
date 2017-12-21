#!/usr/bin/env python
import unittest
from pymodbus.client.async import ModbusSerialClient as ModbusClient
from base_runner import Runner

class AsynchronousAsciiClient(Runner, unittest.TestCase):
    """
    These are the integration tests for the asynchronous
    serial ascii client.
    """

    def setUp(self):
        """ Initializes the test environment """
        super(Runner, self).setUp()
        self.client = ModbusClient(method='ascii')

    def tearDown(self):
        """ Cleans up the test environment """
        self.client.close()
        self.shutdown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
