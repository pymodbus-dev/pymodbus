#!/usr/bin/env python
import unittest
import os
from subprocess import Popen as execute
from pymodbus.datastore.redis import RedisSlaveContext
from base_context import ContextRunner

class RedisSlaveContext(ContextRunner, unittest.TestCase):
    '''
    These are the integration tests for using the redis
    slave context.
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        self.fnull   = open(os.devnull, 'w')
        self.server  = execute("redis-server", stdout=self.fnull, stderr=self.fnull)
        self.context = RedisSlaveContext() # the redis client will block, so no wait needed
        self.initialize()

    def tearDown(self):
        ''' Cleans up the test environment '''
        self.server.kill()
        self.fnull.close()
        self.shutdown()

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
