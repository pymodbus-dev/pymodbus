#!/usr/bin/env python
import unittest
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.datastore.remote import RemoteSlaveContext
from base_context import ContextRunner

class RemoteSlaveContextTest(ContextRunner, unittest.TestCase):
    """
    These are the integration tests for using the redis
    slave context.
    """

    def setUp(self):
        """ Initializes the test environment """
        self.context = RemoteSlaveContext(client=None) # for the log statment
        self.initialize(["../tools/reference/diagslave", "-m", "tcp", "-p", "12345"])
        self.client = ModbusTcpClient(port=12345)
        self.context = RemoteSlaveContext(client=self.client)

    def tearDown(self):
        """ Cleans up the test environment """
        self.client.close()
        self.shutdown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
