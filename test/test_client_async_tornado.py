#!/usr/bin/env python3
"""Test client tornado."""
import unittest
from unittest.mock import patch, Mock
import pytest

from pymodbus.client.asynchronous.tornado import (
    BaseTornadoClient,
    AsyncModbusSerialClient,
    AsyncModbusUDPClient,
    AsyncModbusTCPClient
)
from pymodbus.client.asynchronous import schedulers
from pymodbus.factory import ClientDecoder
from pymodbus.client.asynchronous.twisted import ModbusClientFactory
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer, ModbusRtuFramer
from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse

# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


class AsynchronousClientTest(unittest.TestCase):
    """Unittest for the pymodbus.client.asynchronous module."""

    # -----------------------------------------------------------------------#
    # Test Client client
    # -----------------------------------------------------------------------#

    def test_base_client_init(self):
        """Test the client client initialize"""
        client = BaseTornadoClient()
        self.assertTrue(client.port == 502)
        self.assertTrue(client.host == "127.0.0.1")
        self.assertEqual(0, len(list(client.transaction)))
        self.assertFalse(client._connected)  # pylint: disable=protected-access
        self.assertTrue(client.io_loop is None)
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = BaseTornadoClient(framer=framer, ioloop=schedulers.IO_LOOP)
        self.assertEqual(0, len(list(client.transaction)))
        self.assertFalse(client._connected)  # pylint: disable=protected-access
        self.assertTrue(client.io_loop == schedulers.IO_LOOP)
        self.assertTrue(framer is client.framer)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def test_base_client_on_receive(self, mock_iostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the BaseTornado client data received"""
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        out = []
        data = b'\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04'

        # setup existing request
        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(lambda v: out.append(v))  # pylint: disable=unnecessary-lambda

        client.on_receive(data)
        self.assertTrue(isinstance(response.result(), ReadCoilsResponse))
        data = b''
        out = []
        response = client._build_response(0x01)  # pylint: disable=protected-access
        client.on_receive(data)
        response.add_done_callback(lambda v: out.append(v))  # pylint: disable=unnecessary-lambda
        self.assertFalse(out)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def test_base_client_execute(self, mock_iostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the BaseTornado client execute method"""
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        client.stream = Mock()
        client.stream.write = Mock()

        request = ReadCoilsRequest(1, 1)
        response = client.execute(request)
        tid = request.transaction_id
        self.assertEqual(response, client.transaction.getTransaction(tid))

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def test_base_client_handle_response(self, mock_iostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the BaseTornado client handles responses"""
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        client._handle_response(None)  # pylint: disable=protected-access
        client._handle_response(reply)  # pylint: disable=protected-access

        # handle existing cases
        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(lambda v: out.append(v))  # pylint: disable=unnecessary-lambda
        client._handle_response(reply)  # pylint: disable=protected-access
        self.assertEqual(response.result(), reply)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def test_base_client_build_response(self, mock_iostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the BaseTornado client client builds responses"""
        client = BaseTornadoClient()
        self.assertEqual(0, len(list(client.transaction)))

        def handle_failure(failure):
            exc = failure.exception()
            self.assertTrue(isinstance(exc, ConnectionException))

        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(handle_failure)
        self.assertEqual(0, len(list(client.transaction)))

        client._connected = True  # pylint: disable=protected-access
        client._build_response(0x00)  # pylint: disable=protected-access
        self.assertEqual(1, len(list(client.transaction)))

    # -----------------------------------------------------------------------#
    # Test TCP Client client
    # -----------------------------------------------------------------------#
    def test_tcp_client_init(self):
        """Test the tornado tcp client client initialize"""
        client = AsyncModbusTCPClient()
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = AsyncModbusTCPClient(framer=framer)
        self.assertTrue(framer is client.framer)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def test_tcp_client_connect(self, mock_iostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the tornado tcp client client connect"""
        client = AsyncModbusTCPClient(port=5020)
        self.assertTrue(client.port, 5020)
        self.assertFalse(client._connected)  # pylint: disable=protected-access
        client.connect()
        self.assertTrue(client._connected)  # pylint: disable=protected-access

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def test_tcp_client_disconnect(self, mock_iostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the tornado tcp client client disconnect"""
        client = AsyncModbusTCPClient(port=5020)
        client.connect()

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(handle_failure)

        self.assertTrue(client._connected)  # pylint: disable=protected-access
        client.close()
        self.assertFalse(client._connected)  # pylint: disable=protected-access

    # -----------------------------------------------------------------------#
    # Test Serial Client client
    # -----------------------------------------------------------------------#
    def test_serial_client_init(self):
        """Test the tornado serial client client initialize"""
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=pytest.SERIAL_PORT)
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusRtuFramer))

        framer = object()
        client = AsyncModbusSerialClient(framer=framer)
        self.assertTrue(framer is client.framer)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def test_serial_client_connect(self, mock_serial, mock_seriostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the tornado serial client client connect"""
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=pytest.SERIAL_PORT)
        self.assertTrue(client.port, pytest.SERIAL_PORT)
        self.assertFalse(client._connected)  # pylint: disable=protected-access
        client.connect()
        self.assertTrue(client._connected)  # pylint: disable=protected-access
        client.close()

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def test_serial_client_disconnect(self, mock_serial,  # pylint: disable=unused-argument
                                      mock_seriostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the tornado serial client client disconnect"""
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=pytest.SERIAL_PORT)
        client.connect()
        self.assertTrue(client._connected)  # pylint: disable=protected-access

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(handle_failure)
        client.close()
        self.assertFalse(client._connected)  # pylint: disable=protected-access

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def test_serial_client_execute(self, mock_serial, mock_seriostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the tornado serial client client execute method"""
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=pytest.SERIAL_PORT,
                                         timeout=0)
        client.connect()
        client.stream = Mock()
        client.stream.write = Mock()
        client.stream.connection.read.return_value = b''

        request = ReadCoilsRequest(1, 1)
        response = client.execute(request)
        tid = request.transaction_id
        self.assertEqual(response, client.transaction.getTransaction(tid))

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def test_serial_client_handle_response(self, mock_serial,  # pylint: disable=unused-argument
                                           mock_seriostream, mock_ioloop):  # pylint: disable=unused-argument
        """Test the tornado serial client client handles responses"""
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=pytest.SERIAL_PORT)
        client.connect()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        client._handle_response(None)  # pylint: disable=protected-access
        client._handle_response(reply)  # pylint: disable=protected-access

        # handle existing cases
        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(lambda v: out.append(v))  # pylint: disable=unnecessary-lambda
        client._handle_response(reply)  # pylint: disable=protected-access
        self.assertEqual(response.result(), reply)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def test_serial_client_build_response(self,
                                          mock_serial,  # pylint: disable=unused-argument
                                          mock_seriostream,  # pylint: disable=unused-argument
                                          mock_ioloop):  # pylint: disable=unused-argument
        """Test the tornado serial client client builds responses"""
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=pytest.SERIAL_PORT)
        self.assertEqual(0, len(list(client.transaction)))

        def handle_failure(failure):
            exc = failure.exception()
            self.assertTrue(isinstance(exc, ConnectionException))
        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(handle_failure)
        self.assertEqual(0, len(list(client.transaction)))

        client._connected = True  # pylint: disable=protected-access
        client._build_response(0x00)  # pylint: disable=protected-access
        self.assertEqual(1, len(list(client.transaction)))

    # -----------------------------------------------------------------------#
    # Test Udp Client client
    # -----------------------------------------------------------------------#

    def test_udp_client_init(self):
        """Test the udp client client initialize"""
        client = AsyncModbusUDPClient()
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = AsyncModbusUDPClient(framer=framer)
        self.assertTrue(framer is client.framer)

    # -----------------------------------------------------------------------#
    # Test Client Factories
    # -----------------------------------------------------------------------#

    def test_modbus_client_factory(self):
        """Test the base class for all the clients"""
        factory = ModbusClientFactory()
        self.assertTrue(factory is not None)


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
