#!/usr/bin/env python
import unittest
from pymodbus.client.sync import ModbusUdpClient as ModbusClient
from base_runner import Runner

class SynchronousUdpClient(Runner, unittest.TestCase):
    """
    These are the integration tests for the synchronous
    udp client.
    """

    def setUp(self):
        """ Initializes the test environment """
        super(Runner, self).setUp()
        self.client = ModbusClient()

    def tearDown(self):
        """ Cleans up the test environment """
        self.client.close()
        super(Runner, self).tearDown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
