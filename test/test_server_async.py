#!/usr/bin/env python
from pymodbus.compat import IS_PYTHON3
import unittest
if IS_PYTHON3: # Python 3
    from unittest.mock import patch, Mock
else: # Python 2
    from mock import patch, Mock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.async import ModbusTcpProtocol, ModbusUdpProtocol
from pymodbus.server.async import ModbusServerFactory
from pymodbus.server.async import StartTcpServer, StartUdpServer, StartSerialServer


import sys
#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
SERIAL_PORT = "/dev/ptmx"
if sys.platform == "darwin":
    SERIAL_PORT = "/dev/ptyp0"


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
        values = dict((i, '') for i in range(10))
        identity = ModbusDeviceIdentification(info=values)

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    #-----------------------------------------------------------------------#
    # Test Modbus Server Factory
    #-----------------------------------------------------------------------#

    def testModbusServerFactory(self):
        ''' Test the base class for all the clients '''
        factory = ModbusServerFactory(store=None)
        self.assertEqual(factory.control.Identity.VendorName, '')

        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        factory = ModbusServerFactory(store=None, identity=identity)
        self.assertEqual(factory.control.Identity.VendorName, 'VendorName')

    #-----------------------------------------------------------------------#
    # Test Modbus TCP Server
    #-----------------------------------------------------------------------#
    def testTCPServerDisconnect(self):
        protocol = ModbusTcpProtocol()
        protocol.connectionLost('because of an error')

    #-----------------------------------------------------------------------#
    # Test Modbus UDP Server
    #-----------------------------------------------------------------------#
    def testUdpServerInitialize(self):
        protocol = ModbusUdpProtocol(store=None)
        self.assertEqual(protocol.control.Identity.VendorName, '')

        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        protocol = ModbusUdpProtocol(store=None, identity=identity)
        self.assertEqual(protocol.control.Identity.VendorName, 'VendorName')

    #-----------------------------------------------------------------------#
    # Test Modbus Server Startups
    #-----------------------------------------------------------------------#

    def testTcpServerStartup(self):
        ''' Test that the modbus tcp async server starts correctly '''
        with patch('twisted.internet.reactor') as mock_reactor:
            if IS_PYTHON3:
                console = False
                call_count = 1
            else:
                console = True
                call_count = 2
            StartTcpServer(context=None, console=console)
            self.assertEqual(mock_reactor.listenTCP.call_count, call_count)
            self.assertEqual(mock_reactor.run.call_count, 1)

    def testUdpServerStartup(self):
        ''' Test that the modbus udp async server starts correctly '''
        with patch('twisted.internet.reactor') as mock_reactor:
            StartUdpServer(context=None)
            self.assertEqual(mock_reactor.listenUDP.call_count, 1)
            self.assertEqual(mock_reactor.run.call_count, 1)

    def testSerialServerStartup(self):
        ''' Test that the modbus serial async server starts correctly '''
        with patch('twisted.internet.reactor') as mock_reactor:
            StartSerialServer(context=None, port=SERIAL_PORT)
            self.assertEqual(mock_reactor.run.call_count, 1)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
