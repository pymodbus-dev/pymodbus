#!/usr/bin/env python
import unittest
from pymodbus.datastore.database import DatabaseSlaveContext
from base_context import ContextRunner

class DatabaseSlaveContext(ContextRunner, unittest.TestCase):
    '''
    These are the integration tests for using the redis
    slave context.
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        self.context = DatabaseSlaveContext()
        self.initialize()

    def tearDown(self):
        ''' Cleans up the test environment '''
        # delete database
        self.shutdown()

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
