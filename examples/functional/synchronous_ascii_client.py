#!/usr/bin/env python
import unittest
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from base_runner import Runner

class SynchronousAsciiClient(Runner, unittest.TestCase):
    """
    These are the integration tests for the synchronous
    serial ascii client.
    """

    def setUp(self):
        """ Initializes the test environment """
        super(Runner, self).setUp()
        #    "../tools/nullmodem/linux/run",
        self.initialize(["../tools/reference/diagslave", "-m", "ascii", "/dev/pts/14"])
        self.client = ModbusClient(method='ascii', timeout=0.2, port='/dev/pts/13')
        self.client.connect()

    def tearDown(self):
        """ Cleans up the test environment """
        self.client.close()
        super(Runner, self).tearDown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
