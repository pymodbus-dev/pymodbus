#!/usr/bin/env python
import unittest
from pymodbus.datastore.remote import RemoteSlaveContext
from base_context import ContextRunner

class RemoteSlaveContext(ContextRunner, unittest.TestCase):
    '''
    These are the integration tests for using the redis
    slave context.
    '''

    def setUp(self):
        ''' Initializes the test environment '''
        # start modbus server
        #self.client = ModbusClient(method='ascii')
        self.context = RemoteSlaveContext(client=client)
        self.initialize()

    def tearDown(self):
        ''' Cleans up the test environment '''
        self.client.close()
        self.shutdown()

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
