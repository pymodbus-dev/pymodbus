#!/usr/bin/env python
import unittest, os
from pymodbus.datastore.database import DatabaseSlaveContext
from base_context import ContextRunner

class DatabaseSlaveContextTest(ContextRunner, unittest.TestCase):
    '''
    These are the integration tests for using the redis
    slave context.
    '''
    __database = 'sqlite:///pymodbus-test.db'

    def setUp(self):
        ''' Initializes the test environment '''
        self.context = DatabaseSlaveContext(database=self.__database)
        self.initialize()

    def tearDown(self):
        ''' Cleans up the test environment '''
        os.remove(self.__database.split('///')[1])
        self.shutdown()

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
