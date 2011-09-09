#!/usr/bin/env python
import unittest
from twisted.test import test_protocols
from pymodbus.server.async import ModbusTcpProtocol, ModbusUdpProtocol
from pymodbus.server.async import ModbusServerFactory
from pymodbus.server.async import StartTcpServer, StartUdpServer, StartSerialServer
from pymodbus.exceptions import ConnectionException, NotImplementedException
from pymodbus.exceptions import ParameterException

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class AsynchronousServerTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.server.async module
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
