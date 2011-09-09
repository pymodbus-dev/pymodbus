#!/usr/bin/env python
import unittest
from twisted.test import test_protocols
from pymodbus.client.async import ModbusClientProtocol, ModbusUdpClientProtocol
from pymodbus.client.async import ModbusClientFactory
from pymodbus.exceptions import ConnectionException, NotImplementedException
from pymodbus.exceptions import ParameterException

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class AsynchronousClientTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.client.async module
    '''

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        '''
        Initializes the test environment
        '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    #-----------------------------------------------------------------------#
    # Test Base Client
    #-----------------------------------------------------------------------#

    def testExampleTest(self):
        ''' Test the base class for all the clients '''
        self.assertTrue(True)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
