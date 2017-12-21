#!/usr/bin/env python
import unittest
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from base_runner import Runner

class SynchronousTcpClient(Runner, unittest.TestCase):
    """
    These are the integration tests for the synchronous
    tcp client.
    """

    def setUp(self):
        """ Initializes the test environment """
        self.initialize(["../tools/reference/diagslave", "-m", "tcp", "-p", "12345"])
        self.client = ModbusClient(port=12345)

    def tearDown(self):
        """ Cleans up the test environment """
        self.client.close()
        self.shutdown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
