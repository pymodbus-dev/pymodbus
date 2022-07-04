#!/usr/bin/env python3
"""Test client async twisted."""
import unittest
from unittest.mock import Mock

from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse
from pymodbus.client.asynchronous.twisted import (
    ModbusClientFactory,
    ModbusClientProtocol,
    ModbusSerClientProtocol,
    ModbusTcpClientProtocol,
    ModbusUdpClientProtocol,
)
from pymodbus.exceptions import ConnectionException
from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusRtuFramer, ModbusSocketFramer

# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class AsynchronousClientTest(unittest.TestCase):
    """Unittest for the pymodbus.client.asynchronous module."""

    # -----------------------------------------------------------------------#
    #  Test Client Protocol
    # -----------------------------------------------------------------------#

    def test_client_protocol_init(self):
        """Test the client protocol initialize"""
        protocol = ModbusClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))
        self.assertFalse(protocol._connected)  # pylint: disable=protected-access
        self.assertTrue(isinstance(protocol.framer, ModbusSocketFramer))

        framer = object()
        protocol = ModbusClientProtocol(framer=framer)
        self.assertEqual(0, len(list(protocol.transaction)))
        self.assertFalse(protocol._connected)  # pylint: disable=protected-access
        self.assertTrue(framer is protocol.framer)

    def test_client_protocol_connect(self):
        """Test the client protocol connect"""
        decoder = object()
        framer = ModbusSocketFramer(decoder)
        protocol = ModbusClientProtocol(framer=framer)
        self.assertFalse(protocol._connected)  # pylint: disable=protected-access
        protocol.connectionMade()
        self.assertTrue(protocol._connected)  # pylint: disable=protected-access

    def test_client_protocol_disconnect(self):
        """Test the client protocol disconnect"""
        protocol = ModbusClientProtocol()
        protocol.connectionMade()

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.value, ConnectionException))

        response = protocol._buildResponse(0x00)  # pylint: disable=protected-access
        response.addErrback(handle_failure)

        self.assertTrue(protocol._connected)  # pylint: disable=protected-access
        protocol.connectionLost("because")
        self.assertFalse(protocol._connected)  # pylint: disable=protected-access

    def test_client_protocol_data_received(self):
        """Test the client protocol data received"""
        protocol = ModbusClientProtocol(ModbusSocketFramer(ClientDecoder()))
        protocol.connectionMade()
        out = []
        data = b"\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04"

        # setup existing request
        response = protocol._buildResponse(0x00)  # pylint: disable=protected-access
        response.addCallback(
            lambda v: out.append(v)  # pylint: disable=unnecessary-lambda
        )

        protocol.dataReceived(data)
        self.assertTrue(isinstance(out[0], ReadCoilsResponse))

    def test_client_protocol_execute(self):
        """Test the client protocol execute method"""
        framer = ModbusSocketFramer(None)
        protocol = ModbusClientProtocol(framer=framer)
        protocol.connectionMade()
        protocol.transport = Mock()
        protocol.transport.write = Mock()

        request = ReadCoilsRequest(1, 1)
        response = protocol.execute(request)
        tid = request.transaction_id
        self.assertEqual(response, protocol.transaction.getTransaction(tid))

    def test_client_protocol_handle_response(self):
        """Test the client protocol handles responses"""
        protocol = ModbusClientProtocol()
        protocol.connectionMade()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        protocol._handleResponse(None)  # pylint: disable=protected-access
        protocol._handleResponse(reply)  # pylint: disable=protected-access

        # handle existing cases
        response = protocol._buildResponse(0x00)  # pylint: disable=protected-access
        response.addCallback(
            lambda v: out.append(v)  # pylint: disable=unnecessary-lambda
        )
        protocol._handleResponse(reply)  # pylint: disable=protected-access
        self.assertEqual(out[0], reply)

    def test_client_protocol_build_response(self):
        """Test the udp client protocol builds responses"""
        protocol = ModbusClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.value, ConnectionException))

        response = protocol._buildResponse(0x00)  # pylint: disable=protected-access
        response.addErrback(handle_failure)
        self.assertEqual(0, len(list(protocol.transaction)))

        protocol._connected = True  # pylint: disable=protected-access
        protocol._buildResponse(0x00)  # pylint: disable=protected-access
        self.assertEqual(1, len(list(protocol.transaction)))

    # -----------------------------------------------------------------------#
    #  Test TCP Client Protocol
    # -----------------------------------------------------------------------#
    def test_tcp_client_protocol_init(self):
        """Test the udp client protocol initialize"""
        protocol = ModbusTcpClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))
        self.assertTrue(isinstance(protocol.framer, ModbusSocketFramer))

        framer = object()
        protocol = ModbusClientProtocol(framer=framer)
        self.assertTrue(framer is protocol.framer)

    # -----------------------------------------------------------------------#
    #  Test Serial Client Protocol
    # -----------------------------------------------------------------------#
    def test_serial_client_protocol_init(self):
        """Test the udp client protocol initialize"""
        protocol = ModbusSerClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))
        self.assertTrue(isinstance(protocol.framer, ModbusRtuFramer))

        framer = object()
        protocol = ModbusClientProtocol(framer=framer)
        self.assertTrue(framer is protocol.framer)

    # -----------------------------------------------------------------------#
    #  Test Udp Client Protocol
    # -----------------------------------------------------------------------#

    def test_udp_client_protocol_init(self):
        """Test the udp client protocol initialize"""
        protocol = ModbusUdpClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))
        self.assertTrue(isinstance(protocol.framer, ModbusSocketFramer))

        framer = object()
        protocol = ModbusClientProtocol(framer=framer)
        self.assertTrue(framer is protocol.framer)

    def test_udp_client_protocol_data_received(self):
        """Test the udp client protocol data received"""
        protocol = ModbusUdpClientProtocol()
        out = []
        data = b"\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04"
        server = ("127.0.0.1", 12345)

        # setup existing request
        response = protocol._buildResponse(0x00)  # pylint: disable=protected-access
        response.addCallback(
            lambda v: out.append(v)  # pylint: disable=unnecessary-lambda
        )

        protocol.datagramReceived(data, server)
        self.assertTrue(isinstance(out[0], ReadCoilsResponse))

    def test_udp_client_protocol_execute(self):
        """Test the udp client protocol execute method"""
        protocol = ModbusUdpClientProtocol()
        protocol.transport = Mock()
        protocol.transport.write = Mock()

        request = ReadCoilsRequest(1, 1)
        response = protocol.execute(request)
        tid = request.transaction_id
        self.assertEqual(response, protocol.transaction.getTransaction(tid))

    def test_udp_client_protocol_handle_response(self):
        """Test the udp client protocol handles responses"""
        protocol = ModbusUdpClientProtocol()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        protocol._handleResponse(None)  # pylint: disable=protected-access
        protocol._handleResponse(reply)  # pylint: disable=protected-access

        # handle existing cases
        response = protocol._buildResponse(0x00)  # pylint: disable=protected-access
        response.addCallback(
            lambda v: out.append(v)  # pylint: disable=unnecessary-lambda
        )
        protocol._handleResponse(reply)  # pylint: disable=protected-access
        self.assertEqual(out[0], reply)

    def test_udp_client_protocol_build_response(self):
        """Test the udp client protocol builds responses"""
        protocol = ModbusUdpClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))

        protocol._buildResponse(0x00)  # pylint: disable=protected-access
        self.assertEqual(1, len(list(protocol.transaction)))

    # -----------------------------------------------------------------------#
    #  Test Client Factories
    # -----------------------------------------------------------------------#

    def test_modbus_client_factory(self):
        """Test the base class for all the clients"""
        factory = ModbusClientFactory()
        self.assertTrue(factory is not None)


# ---------------------------------------------------------------------------#
#  Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
