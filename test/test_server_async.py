#!/usr/bin/env python
from pymodbus.compat import IS_PYTHON3
import unittest
if IS_PYTHON3: # Python 3
    from unittest.mock import patch, Mock, MagicMock
else: # Python 2
    from mock import patch, Mock, MagicMock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.async import ModbusTcpProtocol, ModbusUdpProtocol
from pymodbus.server.async import ModbusServerFactory
from pymodbus.server.async import (
    StartTcpServer, StartUdpServer, StartSerialServer, StopServer,
    _is_main_thread
)
from pymodbus.compat import byte2int
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.exceptions import NoSuchSlaveException, ModbusIOException

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
    # Test ModbusTcpProtocol
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

    def testConnectionMade(self):
        protocol = ModbusTcpProtocol()
        protocol.transport = MagicMock()
        protocol.factory = MagicMock()
        protocol.factory.framer = ModbusSocketFramer
        protocol.connectionMade()
        self.assertIsInstance(protocol.framer, ModbusSocketFramer)

    def testConnectionLost(self):
        protocol = ModbusTcpProtocol()
        protocol.connectionLost("What ever reason")

    def testDataReceived(self):
        protocol = ModbusTcpProtocol()
        # mock_data = "Hellow world!"
        mock_data = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        protocol.factory = MagicMock()
        protocol.factory.control.ListenOnly = False
        protocol.factory.store = [byte2int(mock_data[0])]
        protocol.framer = protocol._execute = MagicMock()

        protocol.dataReceived(mock_data)
        # import pdb; pdb.set_trace()
        # protocol.framer.processIncomingPacket.assert_called()
        self.assertTrue(protocol.framer.processIncomingPacket.called)

        # test datareceived returns None
        protocol.factory.control.ListenOnly = False
        self.assertEqual(protocol.dataReceived(mock_data), None)

    def testTcpExecuteSuccess(self):
        protocol = ModbusTcpProtocol()
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()

        # tst  if _send being called
        protocol._execute(request)
        protocol._send.assert_called()

    def testTcpExecuteFailure(self):
        protocol = ModbusTcpProtocol()
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()

        # CASE-1: test NoSuchSlaveException exceptions
        request.execute.side_effect = NoSuchSlaveException()
        self.assertRaises(
            NoSuchSlaveException, protocol._execute(request)
        )
        request.doException.assert_called()

        # CASE-2: NoSuchSlaveException with ignore_missing_slaves = true
        protocol.ignore_missing_slaves = True
        request.execute.side_effect = NoSuchSlaveException()
        self.assertEqual(protocol._execute(request), None)

        # test other exceptions
        request.execute.side_effect = ModbusIOException()
        self.assertRaises(
            ModbusIOException, protocol._execute(request)
        )
        protocol._send.assert_called()

    def testSendTcp(self):

        class MockMsg(object):
            def __init__(self,  msg, resp=False):
                self.should_respond = resp
                self.msg = msg

        mock_msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        protocol = ModbusTcpProtocol()
        mock_data = MockMsg(resp=True, msg=mock_msg)

        protocol.control = MagicMock()
        protocol.framer = MagicMock()
        protocol.factory = MagicMock()
        protocol.framer.buildPacket = MagicMock(return_value=mock_msg)
        protocol.transport= MagicMock()

        protocol._send(mock_data)

        # protocol.framer.buildPacket.assert_called_with(mock_data)
        self.assertTrue(protocol.framer.buildPacket.called)
        protocol.transport.write.assert_called()

        mock_data =MockMsg(resp=False, msg="helloworld")
        self.assertEqual(protocol._send(mock_data), None)

    #-----------------------------------------------------------------------#
    # Test ModbusServerFactory
    #-----------------------------------------------------------------------#
    def testModbusServerFactory(self):
        ''' Test the base class for all the clients '''
        factory = ModbusServerFactory(store=None)
        self.assertEqual(factory.control.Identity.VendorName, '')

        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        factory = ModbusServerFactory(store=None, identity=identity)
        self.assertEqual(factory.control.Identity.VendorName, 'VendorName')

    #-----------------------------------------------------------------------#
    # Test ModbusUdpProtocol
    #-----------------------------------------------------------------------#
    def testUdpServerInitialize(self):
        protocol = ModbusUdpProtocol(store=None)
        self.assertEqual(protocol.control.Identity.VendorName, '')

        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        protocol = ModbusUdpProtocol(store=None, identity=identity)
        self.assertEqual(protocol.control.Identity.VendorName, 'VendorName')


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

    def testDatagramReceived(self):
        mock_data = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        mock_addr = 0x01
        protocol = ModbusUdpProtocol(store=None)
        protocol.framer.processIncomingPacket = MagicMock()
        protocol.control.ListenOnly = False
        protocol._execute = MagicMock()

        protocol.datagramReceived(mock_data, mock_addr)
        # protocol.framer.processIncomingPacket.assert_called()
        self.assertTrue(protocol.framer.processIncomingPacket.called)

    def testSendUdp(self):
        protocol = ModbusUdpProtocol(store=None)
        mock_data = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        mock_addr = 0x01

        protocol.control = MagicMock()
        protocol.framer = MagicMock()
        protocol.framer.buildPacket = MagicMock(return_value=mock_data)
        protocol.transport= MagicMock()

        protocol._send(mock_data, mock_addr)

        # protocol.framer.buildPacket.assert_called_with(mock_data)
        self.assertTrue(protocol.framer.buildPacket.called)
        protocol.transport.write.assert_called()

    def testUdpExecuteSuccess(self):
        protocol = ModbusUdpProtocol(store=None)
        mock_addr = 0x01
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()

        # tst  if _send being called
        protocol._execute(request, mock_addr)
        protocol._send.assert_called()

    def testUdpExecuteFailure(self):
        protocol = ModbusUdpProtocol(store=None)
        mock_addr = 0x01
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()

        # CASE-1: test NoSuchSlaveException exceptions
        request.execute.side_effect = NoSuchSlaveException()
        self.assertRaises(
            NoSuchSlaveException, protocol._execute(request, mock_addr)
        )
        request.doException.assert_called()

        # CASE-2: NoSuchSlaveException with ignore_missing_slaves = true
        protocol.ignore_missing_slaves = True
        request.execute.side_effect = NoSuchSlaveException()
        self.assertEqual(protocol._execute(request, mock_addr), None)

        # test other exceptions
        request.execute.side_effect = ModbusIOException()
        self.assertRaises(
            ModbusIOException, protocol._execute(request, mock_addr)
        )
        protocol._send.assert_called()

    def testStopServer(self):
        from twisted.internet import reactor
        reactor.stop = MagicMock()
        StopServer()

        reactor.stop.assert_called()

    def testIsMainThread(self):
        import threading
        self.assertTrue(_is_main_thread())



#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
