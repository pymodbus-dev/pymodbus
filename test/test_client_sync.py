"""Test client sync."""
import ssl
import unittest
from itertools import count
from test.conftest import mockSocket
from unittest.mock import MagicMock, Mock, patch

import serial

from pymodbus.client import (
    ModbusSerialClient,
    ModbusTcpClient,
    ModbusTlsClient,
    ModbusUdpClient,
)
from pymodbus.client.tls import sslctx_provider
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


class SynchronousClientTest(
    unittest.TestCase
):  # pylint: disable=too-many-public-methods
    """Unittest for the pymodbus.client module."""

    # -----------------------------------------------------------------------#
    # Test UDP Client
    # -----------------------------------------------------------------------#

    def test_basic_syn_udp_client(self):
        """Test the basic methods for the udp sync client"""
        # receive/send
        client = ModbusUdpClient("127.0.0.1")
        client.socket = mockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(1, client.send(b"\x50"))
        self.assertEqual(b"\x50", client.recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("ModbusUdpClient(127.0.0.1:502)", str(client))

    def test_udp_client_is_socket_open(self):
        """Test the udp client is_socket_open method"""
        client = ModbusUdpClient("127.0.0.1")
        self.assertTrue(client.is_socket_open())

    def test_udp_client_send(self):
        """Test the udp client send method"""
        client = ModbusUdpClient("127.0.0.1")
        self.assertRaises(
            ConnectionException,
            lambda: client.send(None),
        )

        client.socket = mockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(4, client.send("1234"))

    def test_udp_client_recv(self):
        """Test the udp client receive method"""
        client = ModbusUdpClient("127.0.0.1")
        self.assertRaises(
            ConnectionException,
            lambda: client.recv(1024),
        )

        client.socket = mockSocket()
        client.socket.mock_store(b"\x00" * 4)
        self.assertEqual(b"", client.recv(0))
        self.assertEqual(b"\x00" * 4, client.recv(4))

    def test_udp_client_repr(self):
        """Test udp client representation."""
        client = ModbusUdpClient("127.0.0.1")
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.params.host}, port={client.params.port}, timeout={client.params.timeout}>"
        )
        self.assertEqual(repr(client), rep)

    # -----------------------------------------------------------------------#
    # Test TCP Client
    # -----------------------------------------------------------------------#

    def test_syn_tcp_client_instantiation(self):
        """Test sync tcp client."""
        client = ModbusTcpClient("127.0.0.1")
        self.assertNotEqual(client, None)

    @patch("pymodbus.client.tcp.select")
    def test_basic_syn_tcp_client(self, mock_select):
        """Test the basic methods for the tcp sync client"""
        # receive/send
        mock_select.select.return_value = [True]
        client = ModbusTcpClient("127.0.0.1")
        client.socket = mockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(1, client.send(b"\x45"))
        self.assertEqual(b"\x45", client.recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("ModbusTcpClient(127.0.0.1:502)", str(client))

    def test_tcp_client_is_socket_open(self):
        """Test the tcp client is_socket_open method"""
        client = ModbusTcpClient("127.0.0.1")
        self.assertFalse(client.is_socket_open())

    def test_tcp_client_send(self):
        """Test the tcp client send method"""
        client = ModbusTcpClient("127.0.0.1")
        self.assertRaises(
            ConnectionException,
            lambda: client.send(None),
        )

        client.socket = mockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(4, client.send("1234"))

    @patch("pymodbus.client.tcp.time")
    @patch("pymodbus.client.tcp.select")
    def test_tcp_client_recv(self, mock_select, mock_time):
        """Test the tcp client receive method"""
        mock_select.select.return_value = [True]
        mock_time.time.side_effect = count()
        client = ModbusTcpClient("127.0.0.1")
        self.assertRaises(
            ConnectionException,
            lambda: client.recv(1024),
        )
        client.socket = mockSocket()
        self.assertEqual(b"", client.recv(0))
        client.socket.mock_store(b"\x00" * 4)
        self.assertEqual(b"\x00" * 4, client.recv(4))

        mock_socket = MagicMock()
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        client.socket = mock_socket
        client.params.timeout = 3
        self.assertEqual(b"\x00\x01\x02", client.recv(3))
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        self.assertEqual(b"\x00\x01", client.recv(2))
        mock_select.select.return_value = [False]
        self.assertEqual(b"", client.recv(2))
        client.socket = mockSocket()
        client.socket.mock_store(b"\x00")
        mock_select.select.return_value = [True]
        self.assertIn(b"\x00", client.recv(None))

        mock_socket = MagicMock()
        mock_socket.recv.return_value = b""
        client.socket = mock_socket
        self.assertRaises(
            ConnectionException,
            lambda: client.recv(1024),
        )

        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02", b""])
        client.socket = mock_socket
        self.assertEqual(b"\x00\x01\x02", client.recv(1024))

    def test_tcp_client_repr(self):
        """Test tcp client."""
        client = ModbusTcpClient("127.0.0.1")
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.params.host}, port={client.params.port}, timeout={client.params.timeout}>"
        )
        self.assertEqual(repr(client), rep)

    def test_tcp_client_register(self):
        """Test tcp client."""

        class CustomRequest:  # pylint: disable=too-few-public-methods
            """Dummy custom request."""

            function_code = 79

        client = ModbusTcpClient("127.0.0.1")
        client.framer = Mock()
        client.register(CustomRequest)
        self.assertTrue(client.framer.decoder.register.called_once_with(CustomRequest))

    # -----------------------------------------------------------------------#
    # Test TLS Client
    # -----------------------------------------------------------------------#

    def test_tls_sslctx_provider(self):
        """Test that sslctx_provider() produce SSLContext correctly"""
        with patch.object(ssl.SSLContext, "load_cert_chain") as mock_method:
            sslctx1 = sslctx_provider(certfile="cert.pem")
            self.assertIsNotNone(sslctx1)
            self.assertEqual(type(sslctx1), ssl.SSLContext)
            self.assertEqual(mock_method.called, False)

            sslctx2 = sslctx_provider(keyfile="key.pem")
            self.assertIsNotNone(sslctx2)
            self.assertEqual(type(sslctx2), ssl.SSLContext)
            self.assertEqual(mock_method.called, False)

            sslctx3 = sslctx_provider(certfile="cert.pem", keyfile="key.pem")
            self.assertIsNotNone(sslctx3)
            self.assertEqual(type(sslctx3), ssl.SSLContext)
            self.assertEqual(mock_method.called, True)

            sslctx_old = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            sslctx_new = sslctx_provider(sslctx=sslctx_old)
            self.assertEqual(sslctx_new, sslctx_old)

    def test_syn_tls_client_instantiation(self):
        """Test sync tls client."""
        # default SSLContext
        client = ModbusTlsClient("127.0.0.1")
        self.assertNotEqual(client, None)
        self.assertIsInstance(client.framer, ModbusTlsFramer)
        self.assertTrue(client.sslctx)

    @patch("pymodbus.client.tcp.select")
    def test_basic_syn_tls_client(self, mock_select):
        """Test the basic methods for the tls sync client"""
        # receive/send
        mock_select.select.return_value = [True]
        client = ModbusTlsClient("localhost")
        client.socket = mockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(1, client.send(b"\x45"))
        self.assertEqual(b"\x45", client.recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()
        self.assertEqual("ModbusTlsClient(localhost:802)", str(client))

        client = ModbusTcpClient("127.0.0.1")
        client.socket = mockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(1, client.send(b"\x45"))
        self.assertEqual(b"\x45", client.recv(1))

    def test_tls_client_send(self):
        """Test the tls client send method"""
        client = ModbusTlsClient("127.0.0.1")
        self.assertRaises(
            ConnectionException,
            lambda: client.send(None),
        )

        client.socket = mockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(4, client.send("1234"))

    @patch("pymodbus.client.tcp.time")
    @patch("pymodbus.client.tcp.select")
    def test_tls_client_recv(self, mock_select, mock_time):
        """Test the tls client receive method"""
        mock_select.select.return_value = [True]
        client = ModbusTlsClient("127.0.0.1")
        self.assertRaises(
            ConnectionException,
            lambda: client.recv(1024),
        )

        mock_time.time.side_effect = count()

        client.socket = mockSocket()
        client.socket.mock_store(b"\x00" * 4)
        self.assertEqual(b"", client.recv(0))
        self.assertEqual(b"\x00" * 4, client.recv(4))

        client.params.timeout = 2
        client.socket.mock_store(b"\x00")
        self.assertIn(b"\x00", client.recv(None))

        # client.socket = mockSocket()
        # client.socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        # client.params.timeout = 3
        # self.assertEqual(
        #     b"\x00\x01\x02", client.recv(3)
        # )
        # client.socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        # self.assertEqual(
        #     b"\x00\x01", client.recv(2)
        # )

    def test_tls_client_repr(self):
        """Test tls client."""
        client = ModbusTlsClient("127.0.0.1")
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.params.host}, port={client.params.port}, sslctx={client.sslctx}, "
            f"timeout={client.params.timeout}>"
        )
        self.assertEqual(repr(client), rep)

    def test_tls_client_register(self):
        """Test tls client."""

        class CustomeRequest:  # pylint: disable=too-few-public-methods
            """Dummy custom request."""

            function_code = 79

        client = ModbusTlsClient("127.0.0.1")
        client.framer = Mock()
        client.register(CustomeRequest)
        self.assertTrue(client.framer.decoder.register.called_once_with(CustomeRequest))

    # -----------------------------------------------------------------------#
    # Test Serial Client
    # -----------------------------------------------------------------------#
    def test_sync_serial_client_instantiation(self):
        """Test sync serial client."""
        client = ModbusSerialClient("/dev/null")
        self.assertNotEqual(client, None)
        self.assertTrue(
            isinstance(
                ModbusSerialClient("/dev/null", framer=ModbusAsciiFramer).framer,
                ModbusAsciiFramer,
            )
        )
        self.assertTrue(
            isinstance(
                ModbusSerialClient("/dev/null", framer=ModbusRtuFramer).framer,
                ModbusRtuFramer,
            )
        )
        self.assertTrue(
            isinstance(
                ModbusSerialClient("/dev/null", framer=ModbusBinaryFramer).framer,
                ModbusBinaryFramer,
            )
        )
        self.assertTrue(
            isinstance(
                ModbusSerialClient("/dev/null", framer=ModbusSocketFramer).framer,
                ModbusSocketFramer,
            )
        )

    def test_sync_serial_rtu_client_timeouts(self):
        """Test sync serial rtu."""
        client = ModbusSerialClient("/dev/null", framer=ModbusRtuFramer, baudrate=9600)
        self.assertEqual(client.silent_interval, round((3.5 * 11 / 9600), 6))
        client = ModbusSerialClient("/dev/null", framer=ModbusRtuFramer, baudrate=38400)
        self.assertEqual(client.silent_interval, round((1.75 / 1000), 6))

    @patch("serial.Serial")
    def test_basic_sync_serial_client(self, mock_serial):
        """Test the basic methods for the serial sync client."""
        # receive/send
        mock_serial.in_waiting = 0
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda

        mock_serial.read = lambda size: b"\x00" * size
        client = ModbusSerialClient("/dev/null")
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client.send(None))
        client.state = 0
        self.assertEqual(1, client.send(b"\x00"))
        self.assertEqual(b"\x00", client.recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # rtu connect/disconnect
        rtu_client = ModbusSerialClient(
            "/dev/null", framer=ModbusRtuFramer, strict=True
        )
        self.assertTrue(rtu_client.connect())
        self.assertEqual(
            rtu_client.socket.interCharTimeout, rtu_client.inter_char_timeout
        )
        rtu_client.close()
        self.assertTrue("baud[19200])" in str(client))

        # already closed socket
        client.socket = False
        client.close()

    def test_serial_client_connect(self):
        """Test the serial client connection method"""
        with patch.object(serial, "Serial") as mock_method:
            mock_method.return_value = MagicMock()
            client = ModbusSerialClient("/dev/null")
            self.assertTrue(client.connect())

        with patch.object(serial, "Serial") as mock_method:
            mock_method.side_effect = serial.SerialException()
            client = ModbusSerialClient("/dev/null")
            self.assertFalse(client.connect())

    @patch("serial.Serial")
    def test_serial_client_is_socket_open(self, mock_serial):
        """Test the serial client is_socket_open method"""
        client = ModbusSerialClient("/dev/null")
        self.assertFalse(client.is_socket_open())
        client.socket = mock_serial
        self.assertTrue(client.is_socket_open())

    @patch("serial.Serial")
    def test_serial_client_send(self, mock_serial):
        """Test the serial client send method"""
        mock_serial.in_waiting = None
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda
        client = ModbusSerialClient("/dev/null")
        self.assertRaises(
            ConnectionException,
            lambda: client.send(None),
        )
        # client.connect()
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client.send(None))
        client.state = 0
        self.assertEqual(4, client.send("1234"))

    @patch("serial.Serial")
    def test_serial_client_cleanup_buffer_before_send(self, mock_serial):
        """Test the serial client send method"""
        mock_serial.in_waiting = 4
        mock_serial.read = lambda x: b"1" * x
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda
        client = ModbusSerialClient("/dev/null")
        self.assertRaises(
            ConnectionException,
            lambda: client.send(None),
        )
        # client.connect()
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client.send(None))
        client.state = 0
        self.assertEqual(4, client.send("1234"))

    def test_serial_client_recv(self):
        """Test the serial client receive method"""
        client = ModbusSerialClient("/dev/null")
        self.assertRaises(
            ConnectionException,
            lambda: client.recv(1024),
        )

        client.socket = mockSocket()
        self.assertEqual(b"", client.recv(0))
        client.socket.mock_store(b"\x00" * 4)
        self.assertEqual(b"\x00" * 4, client.recv(4))
        client.socket = mockSocket()
        client.socket.mock_store(b"")
        self.assertEqual(b"", client.recv(None))
        client.socket.timeout = 0
        self.assertEqual(b"", client.recv(0))

    def test_serial_client_repr(self):
        """Test serial client."""
        client = ModbusSerialClient("/dev/null")
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"framer={client.framer}, timeout={client.params.timeout}>"
        )
        self.assertEqual(repr(client), rep)
