#!/usr/bin/env python
import unittest
import os
from subprocess import Popen as execute
from pymodbus.datastore.modredis import RedisSlaveContext
from base_context import ContextRunner

class RedisSlaveContextTest(ContextRunner, unittest.TestCase):
    """
    These are the integration tests for using the redis
    slave context.
    """

    def setUp(self):
        """ Initializes the test environment """
        self.context = RedisSlaveContext() # the redis client will block, so no wait needed
        self.initialize("redis-server")

    def tearDown(self):
        """ Cleans up the test environment """
        self.server.kill()
        self.fnull.close()
        self.shutdown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
