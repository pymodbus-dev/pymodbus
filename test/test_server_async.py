#!/usr/bin/env python3
"""Test server async."""
import unittest
from unittest.mock import MagicMock

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server.asynchronous import ModbusTcpProtocol, ModbusUdpProtocol
from pymodbus.server.asynchronous import ModbusServerFactory
from pymodbus.server.asynchronous import (
    # TBD    StartTcpServer,
    # TBD    StartUdpServer,
    # TBD    StartSerialServer,
    # TBD    StopServer,
    _is_main_thread,
)
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.exceptions import NoSuchSlaveException, ModbusIOException

# --------------------------------------------------------------------------- #
# Fixture
# --------------------------------------------------------------------------- #


class AsynchronousServerTest(unittest.TestCase):
    """Unittest for the pymodbus.server.asynchronous module."""

    # ----------------------------------------------------------------------- #
    # Setup/TearDown
    # ----------------------------------------------------------------------- #
    def setUp(self):
        """Initialize the test environment."""
        values = {i: "" for i in range(10)}
        ModbusDeviceIdentification(info=values)

    def tearDown(self):
        """Clean up the test environment"""

    # ----------------------------------------------------------------------- #
    # Test ModbusTcpProtocol
    # ----------------------------------------------------------------------- #
    def test_connection_made(self):
        """Test connection made."""
        protocol = ModbusTcpProtocol()
        protocol.transport = MagicMock()
        protocol.factory = MagicMock()
        protocol.factory.framer = ModbusSocketFramer
        protocol.connectionMade()
        self.assertIsInstance(protocol.framer, ModbusSocketFramer)

    def test_connection_lost(self):  # pylint: disable=no-self-use
        """Test connection lost."""
        protocol = ModbusTcpProtocol()
        protocol.connectionLost("What ever reason")

    def test_data_received(self):
        """Test data received."""
        protocol = ModbusTcpProtocol()
        # mock_data = "Hello world!"
        mock_data = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        protocol.factory = MagicMock()
        protocol.factory.control.ListenOnly = False
        protocol.factory.store.slaves = MagicMock()
        protocol.factory.store.single = True
        protocol.factory.store.slaves.return_value = [int(mock_data[6])]
        protocol.framer = protocol._execute = MagicMock()

        protocol.dataReceived(mock_data)
        self.assertTrue(protocol.framer.processIncomingPacket.called)

        # test datareceived returns None
        protocol.factory.control.ListenOnly = False
        self.assertEqual(protocol.dataReceived(mock_data), None)

    def test_tcp_execute_success(self):
        """Test tcp execute."""
        protocol = ModbusTcpProtocol()
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()  # pylint: disable=protected-access

        # test if _send being called
        protocol._execute(request)  # pylint: disable=protected-access
        self.assertTrue(protocol._send.called)  # pylint: disable=protected-access

    def test_tcp_execute_failure(self):
        """Test tcp execute."""
        protocol = ModbusTcpProtocol()
        protocol.factory = MagicMock()
        protocol.factory.store = MagicMock()
        protocol.store = MagicMock()
        protocol.factory.ignore_missing_slaves = False
        request = MagicMock()
        protocol._send = MagicMock()  # pylint: disable=protected-access

        # CASE-1: test NoSuchSlaveException exceptions
        request.execute.side_effect = NoSuchSlaveException()
        protocol._execute(request)  # pylint: disable=protected-access
        self.assertTrue(request.doException.called)

        # CASE-2: NoSuchSlaveException with ignore_missing_slaves = true
        protocol.ignore_missing_slaves = True
        request.execute.side_effect = NoSuchSlaveException()
        self.assertEqual(
            protocol._execute(request), None  # pylint: disable=protected-access
        )

        # test other exceptions
        request.execute.side_effect = ModbusIOException()
        protocol._execute(request)  # pylint: disable=protected-access
        self.assertTrue(protocol._send.called)  # pylint: disable=protected-access

    def test_send_tcp(self):
        """Test send tcp."""

        class MockMsg:  # pylint: disable=too-few-public-methods
            """Mock message."""

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

        protocol._send(mock_data)  # pylint: disable=protected-access

        self.assertTrue(protocol.framer.buildPacket.called)
        self.assertTrue(protocol.transport.write.called)

        mock_data = MockMsg(resp=False, msg="helloworld")
        self.assertEqual(
            protocol._send(mock_data), None  # pylint: disable=protected-access
        )

    # ----------------------------------------------------------------------- #
    # Test ModbusServerFactory
    # ----------------------------------------------------------------------- #
    def test_modbus_server_factory(self):
        """Test the base class for all the clients"""
        factory = ModbusServerFactory(store=None)
        self.assertEqual(factory.control.Identity.VendorName, "")

        identity = ModbusDeviceIdentification(info_name={"VendorName": "VendorName"})
        factory = ModbusServerFactory(store=None, identity=identity)
        self.assertEqual(factory.control.Identity.VendorName, "VendorName")

    # ----------------------------------------------------------------------- #
    # Test ModbusUdpProtocol
    # ----------------------------------------------------------------------- #
    def test_udp_server_initialize(self):
        """Test UDP server."""
        protocol = ModbusUdpProtocol(store=None)
        self.assertEqual(protocol.control.Identity.VendorName, "")

        identity = ModbusDeviceIdentification(info={0x00: "VendorName"})
        protocol = ModbusUdpProtocol(store=None, identity=identity)
        self.assertEqual(protocol.control.Identity.VendorName, "VendorName")

    def test_datagram_received(self):
        """Test datagram received."""
        mock_data = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        mock_addr = 0x01
        protocol = ModbusUdpProtocol(store=None)
        protocol.framer.processIncomingPacket = MagicMock()
        protocol.control.ListenOnly = False
        protocol._execute = MagicMock()  # pylint: disable=protected-access

        protocol.datagramReceived(mock_data, mock_addr)
        self.assertTrue(protocol.framer.processIncomingPacket.called)

    def test_send_udp(self):
        """Test send UDP."""
        protocol = ModbusUdpProtocol(store=None)
        mock_data = b"\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        mock_addr = 0x01

        protocol.control = MagicMock()
        protocol.framer = MagicMock()
        protocol.framer.buildPacket = MagicMock(return_value=mock_data)
        protocol.transport = MagicMock()

        protocol._send(mock_data, mock_addr)  # pylint: disable=protected-access

        self.assertTrue(protocol.framer.buildPacket.called)
        self.assertTrue(protocol.transport.write.called)

    def test_udp_execute_success(self):
        """Test UDP execute success."""
        protocol = ModbusUdpProtocol(store=None)
        mock_addr = 0x01
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()  # pylint: disable=protected-access

        # test if _send being called
        protocol._execute(request, mock_addr)  # pylint: disable=protected-access
        self.assertTrue(protocol._send.called)  # pylint: disable=protected-access

    def test_udp_execute_failure(self):
        """Test UDP execute failure."""
        protocol = ModbusUdpProtocol(store=None)
        mock_addr = 0x01
        protocol.store = MagicMock()
        request = MagicMock()
        protocol._send = MagicMock()  # pylint: disable=protected-access

        # CASE-1: test NoSuchSlaveException exceptions
        request.execute.side_effect = NoSuchSlaveException()
        protocol._execute(request, mock_addr)  # pylint: disable=protected-access
        self.assertTrue(request.doException.called)

        # CASE-2: NoSuchSlaveException with ignore_missing_slaves = true
        protocol.ignore_missing_slaves = True
        request.execute.side_effect = NoSuchSlaveException()
        self.assertEqual(
            protocol._execute(request, mock_addr), None  # pylint: disable=protected-access
        )

        # test other exceptions
        request.execute.side_effect = ModbusIOException()
        protocol._execute(request, mock_addr)  # pylint: disable=protected-access
        self.assertTrue(protocol._send.called)  # pylint: disable=protected-access

    def test_is_main_thread(self):
        """Test is main thread."""
        self.assertTrue(_is_main_thread())


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
