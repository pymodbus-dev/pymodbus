#!/usr/bin/env python
from pymodbus.compat import IS_PYTHON3
import unittest
import pytest
if IS_PYTHON3:  # Python 3
    from unittest.mock import patch, MagicMock
else:  # Python 2
    from mock import patch, MagicMock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.asynchronous import ModbusTcpProtocol, ModbusUdpProtocol
from pymodbus.server.asynchronous import ModbusServerFactory
from pymodbus.server.asynchronous import (
    StartTcpServer, StartUdpServer, StartSerialServer, StopServer,
    _is_main_thread
)
from pymodbus.compat import byte2int
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.exceptions import NoSuchSlaveException, ModbusIOException

import sys
# --------------------------------------------------------------------------- #
# Fixture
# --------------------------------------------------------------------------- #
import platform
from pkg_resources import parse_version

IS_DARWIN = platform.system().lower() == "darwin"
OSX_SIERRA = parse_version("10.12")
if IS_DARWIN:
    IS_HIGH_SIERRA_OR_ABOVE = OSX_SIERRA < parse_version(platform.mac_ver()[0])
    SERIAL_PORT = '/dev/ptyp0' if not IS_HIGH_SIERRA_OR_ABOVE else '/dev/ttyp0'
else:
    IS_HIGH_SIERRA_OR_ABOVE = False
    SERIAL_PORT = "/dev/ptmx"

no_twisted_serial_on_windows_with_pypy = pytest.mark.skipif(
    sys.platform == 'win32' and platform.python_implementation() == 'PyPy',
    reason='Twisted serial requires pywin32 which is not compatible with PyPy',
)


class AsynchronousServerTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.server.asynchronous module
    '''

    # ----------------------------------------------------------------------- #
    # Setup/TearDown
    # ----------------------------------------------------------------------- #
    def setUp(self):
        '''
        Initializes the test environment
        '''
        values = dict((i, '') for i in range(10))
        identity = ModbusDeviceIdentification(info=values)

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    # ----------------------------------------------------------------------- #
    # Test ModbusTcpProtocol
    # ----------------------------------------------------------------------- #
    def testTcpServerStartup(self):
        ''' Test that the modbus tcp asynchronous server starts correctly '''
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
        protocol.factory.store.slaves = MagicMock()
        protocol.factory.store.single = True
        protocol.factory.store.slaves.return_value = [byte2int(mock_data[6])]
        protocol.framer = protocol._execute = MagicMock()

        protocol.dataReceived(mock_data)
        self.assertTrue(protocol.framer.processIncomingPacket.called)

        # test datareceived returns None
        protocol.factory.control.ListenOnly = False
        self.assertEqual(protocol.dataReceived(mock_data), None)

    def testTcpExecuteSuccess(self):
        protocol = ModbusTcpProtocol()
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()

        # test if _send being called
        protocol._execute(request)
        self.assertTrue(protocol._send.called)

    def testTcpExecuteFailure(self):
        protocol = ModbusTcpProtocol()
        protocol.factory = MagicMock()
        protocol.factory.store = MagicMock()
        protocol.store = MagicMock()
        protocol.factory.ignore_missing_slaves = False
        request = MagicMock()
        protocol._send = MagicMock()

        # CASE-1: test NoSuchSlaveException exceptions
        request.execute.side_effect = NoSuchSlaveException()
        protocol._execute(request)
        self.assertTrue(request.doException.called)

        # CASE-2: NoSuchSlaveException with ignore_missing_slaves = true
        protocol.ignore_missing_slaves = True
        request.execute.side_effect = NoSuchSlaveException()
        self.assertEqual(protocol._execute(request), None)

        # test other exceptions
        request.execute.side_effect = ModbusIOException()
        protocol._execute(request)
        self.assertTrue(protocol._send.called)

    def testSendTcp(self):

        class MockMsg(object):
            def __init__(self, msg, resp=False):
                self.should_respond = resp
                self.msg = msg

        mock_msg = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        protocol = ModbusTcpProtocol()
        mock_data = MockMsg(resp=True, msg=mock_msg)

        protocol.control = MagicMock()
        protocol.framer = MagicMock()
        protocol.factory = MagicMock()
        protocol.framer.buildPacket = MagicMock(return_value=mock_msg)
        protocol.transport = MagicMock()

        protocol._send(mock_data)

        self.assertTrue(protocol.framer.buildPacket.called)
        self.assertTrue(protocol.transport.write.called)

        mock_data = MockMsg(resp=False, msg="helloworld")
        self.assertEqual(protocol._send(mock_data), None)

    # ----------------------------------------------------------------------- #
    # Test ModbusServerFactory
    # ----------------------------------------------------------------------- #
    def testModbusServerFactory(self):
        ''' Test the base class for all the clients '''
        factory = ModbusServerFactory(store=None)
        self.assertEqual(factory.control.Identity.VendorName, '')

        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        factory = ModbusServerFactory(store=None, identity=identity)
        self.assertEqual(factory.control.Identity.VendorName, 'VendorName')

    # ----------------------------------------------------------------------- #
    # Test ModbusUdpProtocol
    # ----------------------------------------------------------------------- #
    def testUdpServerInitialize(self):
        protocol = ModbusUdpProtocol(store=None)
        self.assertEqual(protocol.control.Identity.VendorName, '')

        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        protocol = ModbusUdpProtocol(store=None, identity=identity)
        self.assertEqual(protocol.control.Identity.VendorName, 'VendorName')

    def testUdpServerStartup(self):
        ''' Test that the modbus udp asynchronous server starts correctly '''
        with patch('twisted.internet.reactor') as mock_reactor:
            StartUdpServer(context=None)
            self.assertEqual(mock_reactor.listenUDP.call_count, 1)
            self.assertEqual(mock_reactor.run.call_count, 1)

    @no_twisted_serial_on_windows_with_pypy
    @patch("twisted.internet.serialport.SerialPort")
    def testSerialServerStartup(self, mock_sp):
        ''' Test that the modbus serial asynchronous server starts correctly '''
        with patch('twisted.internet.reactor') as mock_reactor:
            StartSerialServer(context=None, port=SERIAL_PORT)
            self.assertEqual(mock_reactor.run.call_count, 1)

    @no_twisted_serial_on_windows_with_pypy
    @patch("twisted.internet.serialport.SerialPort")
    def testStopServerFromMainThread(self, mock_sp):
        """
        Stop asynchronous server
        :return:
        """
        with patch('twisted.internet.reactor') as mock_reactor:
            StartSerialServer(context=None, port=SERIAL_PORT)
            self.assertEqual(mock_reactor.run.call_count, 1)
            StopServer()
            self.assertEqual(mock_reactor.stop.call_count, 1)

    @no_twisted_serial_on_windows_with_pypy
    @patch("twisted.internet.serialport.SerialPort")
    def testStopServerFromThread(self, mock_sp):
        """
        Stop asynchronous server from child thread
        :return:
        """
        from threading import Thread
        import time
        with patch('twisted.internet.reactor') as mock_reactor:
            StartSerialServer(context=None, port=SERIAL_PORT)
            self.assertEqual(mock_reactor.run.call_count, 1)
            t = Thread(target=StopServer)
            t.start()
            time.sleep(2)
            self.assertEqual(mock_reactor.callFromThread.call_count, 1)

    def testDatagramReceived(self):
        mock_data = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        mock_addr = 0x01
        protocol = ModbusUdpProtocol(store=None)
        protocol.framer.processIncomingPacket = MagicMock()
        protocol.control.ListenOnly = False
        protocol._execute = MagicMock()

        protocol.datagramReceived(mock_data, mock_addr)
        self.assertTrue(protocol.framer.processIncomingPacket.called)

    def testSendUdp(self):
        protocol = ModbusUdpProtocol(store=None)
        mock_data = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        mock_addr = 0x01

        protocol.control = MagicMock()
        protocol.framer = MagicMock()
        protocol.framer.buildPacket = MagicMock(return_value=mock_data)
        protocol.transport = MagicMock()

        protocol._send(mock_data, mock_addr)

        self.assertTrue(protocol.framer.buildPacket.called)
        self.assertTrue(protocol.transport.write.called)

    def testUdpExecuteSuccess(self):
        protocol = ModbusUdpProtocol(store=None)
        mock_addr = 0x01
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()

        # test if _send being called
        protocol._execute(request, mock_addr)
        self.assertTrue(protocol._send.called)

    def testUdpExecuteFailure(self):
        protocol = ModbusUdpProtocol(store=None)
        mock_addr = 0x01
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()

        # CASE-1: test NoSuchSlaveException exceptions
        request.execute.side_effect = NoSuchSlaveException()
        protocol._execute(request, mock_addr)
        self.assertTrue(request.doException.called)

        # CASE-2: NoSuchSlaveException with ignore_missing_slaves = true
        protocol.ignore_missing_slaves = True
        request.execute.side_effect = NoSuchSlaveException()
        self.assertEqual(protocol._execute(request, mock_addr), None)

        # test other exceptions
        request.execute.side_effect = ModbusIOException()
        protocol._execute(request, mock_addr)
        self.assertTrue(protocol._send.called)

    def testStopServer(self):
        from twisted.internet import reactor
        reactor.stop = MagicMock()
        StopServer()

        self.assertTrue(reactor.stop.called)

    def testIsMainThread(self):
        self.assertTrue(_is_main_thread())


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
