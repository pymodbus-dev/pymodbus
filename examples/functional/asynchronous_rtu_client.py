#!/usr/bin/env python
import unittest
from pymodbus.client.async import ModbusSerialClient as ModbusClient
from base_runner import Runner

class AsynchronousRtuClient(Runner, unittest.TestCase):
    """
    These are the integration tests for the asynchronous
    serial rtu client.
    """

    def setUp(self):
        """ Initializes the test environment """
        super(Runner, self).setUp()
        self.client = ModbusClient(method='rtu')

    def tearDown(self):
        """ Cleans up the test environment """
        self.client.close()
        super(Runner, self).tearDown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
