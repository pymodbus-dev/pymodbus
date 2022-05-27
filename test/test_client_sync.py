#!/usr/bin/env python3
"""Test client sync."""
import socket
import ssl
import sys
from io import StringIO
from itertools import count
from unittest.mock import patch, Mock, MagicMock
import unittest
import pytest
import serial

from pymodbus.client.sync import ModbusTcpClient, ModbusUdpClient
from pymodbus.client.sync import ModbusSerialClient, BaseModbusClient
from pymodbus.client.sync import ModbusTlsClient
from pymodbus.client.tls_helper import sslctx_provider
from pymodbus.exceptions import ConnectionException, NotImplementedException
from pymodbus.exceptions import ParameterException
from pymodbus.transaction import ModbusAsciiFramer, ModbusRtuFramer
from pymodbus.transaction import ModbusBinaryFramer
from pymodbus.transaction import ModbusSocketFramer, ModbusTlsFramer
from pymodbus.utilities import hexlify_packets


# ---------------------------------------------------------------------------#
# Mock Classes
# ---------------------------------------------------------------------------#
class mockSocket:  # NOSONAR pylint: disable=invalid-name
    """Mock socket."""

    timeout = 2

    def close(self):  # pylint: disable=no-self-use
        """Close."""
        return True

    def recv(self, size):  # pylint: disable=no-self-use
        """Receive."""
        return b"\x00" * size

    def read(self, size):  # pylint: disable=no-self-use
        """Read."""
        return b"\x00" * size

    def send(self, msg):  # pylint: disable=no-self-use
        """Send."""
        return len(msg)

    def write(self, msg):  # pylint: disable=no-self-use
        """Write."""
        return len(msg)

    def recvfrom(self, size):  # pylint: disable=no-self-use
        """Receive from."""
        return [b"\x00" * size]

    def sendto(self, msg, *args):  # NOSONAR pylint: disable=no-self-use,unused-argument
        """Send to."""
        return len(msg)

    def setblocking(self, flag):  # NOSONAR pylint: disable=no-self-use,unused-argument
        """Set blocking."""
        return None

    def in_waiting(self):  # pylint: disable=no-self-use
        """Do in waiting."""
        return None


inet_pton_skipif = pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info < (3, 4),
    reason=("Uses socket.inet_pton() which wasn't available on Windows until 3.4.",),
)


# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#
class SynchronousClientTest(
    unittest.TestCase
):  # pylint: disable=too-many-public-methods
    """Unittest for the pymodbus.client.sync module."""

    # -----------------------------------------------------------------------#
    # Test Base Client
    # -----------------------------------------------------------------------#

    def test_base_modbus_client(self):
        """Test the base class for all the clients"""
        client = BaseModbusClient(None)
        client.transaction = None
        self.assertRaises(
            NotImplementedException, lambda: client.connect()  # pylint: disable=unnecessary-lambda

        )
        self.assertRaises(NotImplementedException, lambda: client.send(None))
        self.assertRaises(NotImplementedException, lambda: client.recv(None))
        self.assertRaises(
            NotImplementedException, lambda: client.__enter__()  # pylint: disable=unnecessary-lambda
        )
        self.assertRaises(
            NotImplementedException, lambda: client.execute()  # pylint: disable=unnecessary-lambda
        )
        self.assertRaises(
            NotImplementedException, lambda: client.is_socket_open()  # pylint: disable=unnecessary-lambda
        )
        self.assertEqual("Null Transport", str(client))
        client.close()
        client.__exit__(0, 0, 0)

        # Test information methods
        client.last_frame_end = 2
        client.silent_interval = 2
        self.assertEqual(4, client.idle_time())
        client.last_frame_end = None
        self.assertEqual(0, client.idle_time())

        # Test debug/trace/_dump methods
        self.assertEqual(False, client.debug_enabled())
        writable = StringIO()
        client.trace(writable)
        client._dump(b"\x00\x01\x02")  # pylint: disable=protected-access
        self.assertEqual(hexlify_packets(b"\x00\x01\x02"), writable.getvalue())

        # a successful execute
        client.connect = lambda: True
        client.transaction = Mock(**{"execute.return_value": True})
        self.assertEqual(client, client.__enter__())
        self.assertTrue(client.execute())

        # a unsuccessful connect
        client.connect = lambda: False
        self.assertRaises(
            ConnectionException, lambda: client.__enter__()  # pylint: disable=unnecessary-lambda
        )
        self.assertRaises(
            ConnectionException, lambda: client.execute()  # pylint: disable=unnecessary-lambda
        )

    # -----------------------------------------------------------------------#
    # Test UDP Client
    # -----------------------------------------------------------------------#

    def test_sync_udp_client_instantiation(self):
        """Test sync udp clientt."""
        client = ModbusUdpClient()
        self.assertNotEqual(client, None)

    def tes_basic_sync_udp_client(self):
        """Test the basic methods for the udp sync client"""
        # receive/send
        client = ModbusUdpClient()
        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        self.assertEqual(1, client._send(b"\x00"))  # pylint: disable=protected-access
        self.assertEqual(b"\x00", client._recv(1))  # pylint: disable=protected-access

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("ModbusUdpClient(127.0.0.1:502)", str(client))

    @inet_pton_skipif
    def test_udp_client_address_family(self):
        """Test the Udp client get address family method"""
        client = ModbusUdpClient()
        self.assertEqual(
            socket.AF_INET, client._get_address_family("127.0.0.1")  # pylint: disable=protected-access
        )
        self.assertEqual(
            socket.AF_INET6, client._get_address_family("::1")  # pylint: disable=protected-access
        )

    @inet_pton_skipif
    def test_udp_client_connect(self):
        """Test the Udp client connection method"""
        with patch.object(socket, "socket") as mock_method:

            class DummySocket:  # pylint: disable=too-few-public-methods
                """Dummy socket."""

                def settimeout(self, *a, **kwa):
                    """Set timeout."""

            mock_method.return_value = DummySocket()
            client = ModbusUdpClient()
            self.assertTrue(client.connect())

        with patch.object(socket, "socket") as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusUdpClient()
            self.assertFalse(client.connect())

    @inet_pton_skipif
    def test_udp_client_is_socket_open(self):
        """Test the udp client is_socket_open method"""
        client = ModbusUdpClient()
        self.assertTrue(client.is_socket_open())

    def test_udp_client_send(self):
        """Test the udp client send method"""
        client = ModbusUdpClient()
        self.assertRaises(
            ConnectionException, lambda: client._send(None)  # pylint: disable=protected-access
        )

        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        self.assertEqual(4, client._send("1234"))  # pylint: disable=protected-access

    def test_udp_client_recv(self):
        """Test the udp client receive method"""
        client = ModbusUdpClient()
        self.assertRaises(
            ConnectionException, lambda: client._recv(1024)  # pylint: disable=protected-access
        )

        client.socket = mockSocket()
        self.assertEqual(b"", client._recv(0))  # pylint: disable=protected-access
        self.assertEqual(
            b"\x00" * 4, client._recv(4)  # pylint: disable=protected-access
        )

    def test_udp_client_repr(self):
        """Test udp client representation."""
        client = ModbusUdpClient()
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.host}, port={client.port}, timeout={client.timeout}>"
        )
        self.assertEqual(repr(client), rep)

    # -----------------------------------------------------------------------#
    # Test TCP Client
    # -----------------------------------------------------------------------#

    def test_sync_tcp_client_instantiation(self):
        """Test sync tcp client."""
        client = ModbusTcpClient()
        self.assertNotEqual(client, None)

    @patch("pymodbus.client.sync.select")
    def test_basic_sync_tcp_client(self, mock_select):
        """Test the basic methods for the tcp sync client"""
        # receive/send
        mock_select.select.return_value = [True]
        client = ModbusTcpClient()
        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        self.assertEqual(1, client._send(b"\x00"))  # pylint: disable=protected-access
        self.assertEqual(b"\x00", client._recv(1))  # pylint: disable=protected-access

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("ModbusTcpClient(127.0.0.1:502)", str(client))

    def test_tcp_client_connect(self):
        """Test the tcp client connection method"""
        with patch.object(socket, "create_connection") as mock_method:
            _socket = MagicMock()
            mock_method.return_value = _socket
            client = ModbusTcpClient()
            _socket.getsockname.return_value = ("dmmy", 1234)
            self.assertTrue(client.connect())

        with patch.object(socket, "create_connection") as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusTcpClient()
            self.assertFalse(client.connect())

    def test_tcp_client_is_socket_open(self):
        """Test the tcp client is_socket_open method"""
        client = ModbusTcpClient()
        self.assertFalse(client.is_socket_open())

    def test_tcp_client_send(self):
        """Test the tcp client send method"""
        client = ModbusTcpClient()
        self.assertRaises(
            ConnectionException, lambda: client._send(None)  # pylint: disable=protected-access
        )

        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        self.assertEqual(4, client._send("1234"))  # pylint: disable=protected-access

    @patch("pymodbus.client.sync.time")
    @patch("pymodbus.client.sync.select")
    def test_tcp_client_recv(self, mock_select, mock_time):
        """Test the tcp client receive method"""
        mock_select.select.return_value = [True]
        mock_time.time.side_effect = count()
        client = ModbusTcpClient()
        self.assertRaises(
            ConnectionException, lambda: client._recv(1024)  # pylint: disable=protected-access
        )

        client.socket = mockSocket()
        self.assertEqual(b"", client._recv(0))  # pylint: disable=protected-access
        self.assertEqual(
            b"\x00" * 4, client._recv(4)  # pylint: disable=protected-access
        )

        mock_socket = MagicMock()
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        client.socket = mock_socket
        client.timeout = 3
        self.assertEqual(
            b"\x00\x01\x02", client._recv(3)  # pylint: disable=protected-access
        )
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        self.assertEqual(
            b"\x00\x01", client._recv(2)  # pylint: disable=protected-access
        )
        mock_select.select.return_value = [False]
        self.assertEqual(b"", client._recv(2))  # pylint: disable=protected-access
        client.socket = mockSocket()
        mock_select.select.return_value = [True]
        self.assertIn(b"\x00", client._recv(None))  # pylint: disable=protected-access

        mock_socket = MagicMock()
        mock_socket.recv.return_value = b""
        client.socket = mock_socket
        self.assertRaises(
            ConnectionException, lambda: client._recv(1024)  # pylint: disable=protected-access
        )

        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02", b""])
        client.socket = mock_socket
        self.assertEqual(
            b"\x00\x01\x02", client._recv(1024)  # pylint: disable=protected-access
        )

    def test_tcp_client_repr(self):
        """Test tcp client."""
        client = ModbusTcpClient()
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.host}, port={client.port}, timeout={client.timeout}>"
        )
        self.assertEqual(repr(client), rep)

    def test_tcp_client_register(self):
        """Test tcp client."""

        class CustomRequest:  # pylint: disable=too-few-public-methods
            """Dummy custom request."""

            function_code = 79

        client = ModbusTcpClient()
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

    def test_sync_tls_client_instantiation(self):
        """Test sync tls client."""
        # default SSLContext
        client = ModbusTlsClient()
        self.assertNotEqual(client, None)
        self.assertIsInstance(client.framer, ModbusTlsFramer)
        self.assertTrue(client.sslctx)

    def test_basic_sync_tls_client(self):
        """Test the basic methods for the tls sync client"""
        # receive/send
        client = ModbusTlsClient()
        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        self.assertEqual(1, client._send(b"\x00"))  # pylint: disable=protected-access
        self.assertEqual(b"\x00", client._recv(1))  # pylint: disable=protected-access

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("ModbusTlsClient(localhost:802)", str(client))

    def test_tls_client_connect(self):
        """Test the tls client connection method"""
        with patch.object(ssl.SSLSocket, "connect") as mock_method:
            client = ModbusTlsClient()
            self.assertTrue(client.connect())

        with patch.object(socket, "create_connection") as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusTlsClient()
            self.assertFalse(client.connect())

    def test_tls_client_send(self):
        """Test the tls client send method"""
        client = ModbusTlsClient()
        self.assertRaises(
            ConnectionException, lambda: client._send(None)  # pylint: disable=protected-access
        )

        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        self.assertEqual(4, client._send("1234"))  # pylint: disable=protected-access

    @patch("pymodbus.client.sync.time")
    def test_tls_client_recv(self, mock_time):
        """Test the tls client receive method"""
        client = ModbusTlsClient()
        self.assertRaises(
            ConnectionException, lambda: client._recv(1024)  # pylint: disable=protected-access
        )

        mock_time.time.side_effect = count()

        client.socket = mockSocket()
        self.assertEqual(b"", client._recv(0))  # pylint: disable=protected-access
        self.assertEqual(
            b"\x00" * 4, client._recv(4)  # pylint: disable=protected-access
        )

        client.timeout = 2
        self.assertIn(b"\x00", client._recv(None))  # pylint: disable=protected-access

        mock_socket = MagicMock()
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        client.socket = mock_socket
        client.timeout = 3
        self.assertEqual(
            b"\x00\x01\x02", client._recv(3)  # pylint: disable=protected-access
        )
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        self.assertEqual(
            b"\x00\x01", client._recv(2)  # pylint: disable=protected-access
        )

    def test_tls_client_repr(self):
        """Test tls client."""
        client = ModbusTlsClient()
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"ipaddr={client.host}, port={client.port}, sslctx={client.sslctx}, "
            f"timeout={client.timeout}>"
        )
        self.assertEqual(repr(client), rep)

    def test_tls_client_register(self):
        """Test tls client."""

        class CustomeRequest:  # pylint: disable=too-few-public-methods
            """Dummy custom request."""

            function_code = 79

        client = ModbusTlsClient()
        client.framer = Mock()
        client.register(CustomeRequest)
        self.assertTrue(client.framer.decoder.register.called_once_with(CustomeRequest))

    # -----------------------------------------------------------------------#
    # Test Serial Client
    # -----------------------------------------------------------------------#

    def test_sync_serial_client_instantiation(self):
        """Test sync serial client."""
        client = ModbusSerialClient()
        self.assertNotEqual(client, None)
        self.assertTrue(
            isinstance(ModbusSerialClient(method="ascii").framer, ModbusAsciiFramer)
        )
        self.assertTrue(
            isinstance(ModbusSerialClient(method="rtu").framer, ModbusRtuFramer)
        )
        self.assertTrue(
            isinstance(ModbusSerialClient(method="binary").framer, ModbusBinaryFramer)
        )
        self.assertTrue(
            isinstance(ModbusSerialClient(method="socket").framer, ModbusSocketFramer)
        )
        self.assertRaises(
            ParameterException, lambda: ModbusSerialClient(method="something")
        )

    def test_sync_serial_rtu_client_timeouts(self):
        """Test sync serial rtu."""
        client = ModbusSerialClient(method="rtu", baudrate=9600)
        self.assertEqual(client.silent_interval, round((3.5 * 11 / 9600), 6))
        client = ModbusSerialClient(method="rtu", baudrate=38400)
        self.assertEqual(client.silent_interval, round((1.75 / 1000), 6))

    @patch("serial.Serial")
    def test_basic_sync_serial_client(self, mock_serial):
        """Test the basic methods for the serial sync client."""
        # receive/send
        mock_serial.in_waiting = 0
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda

        mock_serial.read = lambda size: b"\x00" * size
        client = ModbusSerialClient()
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        client.state = 0
        self.assertEqual(1, client._send(b"\x00"))  # pylint: disable=protected-access
        self.assertEqual(b"\x00", client._recv(1))  # pylint: disable=protected-access

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # rtu connect/disconnect
        rtu_client = ModbusSerialClient(method="rtu", strict=True)
        self.assertTrue(rtu_client.connect())
        self.assertEqual(
            rtu_client.socket.interCharTimeout, rtu_client.inter_char_timeout
        )
        rtu_client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("ModbusSerialClient(ascii baud[19200])", str(client))

    def test_serial_client_connect(self):
        """Test the serial client connection method"""
        with patch.object(serial, "Serial") as mock_method:
            mock_method.return_value = MagicMock()
            client = ModbusSerialClient()
            self.assertTrue(client.connect())

        with patch.object(serial, "Serial") as mock_method:
            mock_method.side_effect = serial.SerialException()
            client = ModbusSerialClient()
            self.assertFalse(client.connect())

    @patch("serial.Serial")
    def test_serial_client_is_socket_open(self, mock_serial):
        """Test the serial client is_socket_open method"""
        client = ModbusSerialClient()
        self.assertFalse(client.is_socket_open())
        client.socket = mock_serial
        self.assertTrue(client.is_socket_open())

    @patch("serial.Serial")
    def test_serial_client_send(self, mock_serial):
        """Test the serial client send method"""
        mock_serial.in_waiting = None
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda
        client = ModbusSerialClient()
        self.assertRaises(
            ConnectionException, lambda: client._send(None)  # pylint: disable=protected-access
        )
        # client.connect()
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        client.state = 0
        self.assertEqual(4, client._send("1234"))  # pylint: disable=protected-access

    @patch("serial.Serial")
    def test_serial_client_cleanup_buffer_before_send(self, mock_serial):
        """Test the serial client send method"""
        mock_serial.in_waiting = 4
        mock_serial.read = lambda x: b"1" * x
        mock_serial.write = lambda x: len(x)  # pylint: disable=unnecessary-lambda
        client = ModbusSerialClient()
        self.assertRaises(
            ConnectionException, lambda: client._send(None)  # pylint: disable=protected-access
        )
        # client.connect()
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client._send(None))  # pylint: disable=protected-access
        client.state = 0
        self.assertEqual(4, client._send("1234"))  # pylint: disable=protected-access

    def test_serial_client_recv(self):
        """Test the serial client receive method"""
        client = ModbusSerialClient()
        self.assertRaises(
            ConnectionException, lambda: client._recv(1024)  # pylint: disable=protected-access
        )

        client.socket = mockSocket()
        self.assertEqual(b"", client._recv(0))  # pylint: disable=protected-access
        self.assertEqual(
            b"\x00" * 4, client._recv(4)  # pylint: disable=protected-access
        )
        client.socket = MagicMock()
        client.socket.read.return_value = b""
        self.assertEqual(b"", client._recv(None))  # pylint: disable=protected-access
        client.socket.timeout = 0
        self.assertEqual(b"", client._recv(0))  # pylint: disable=protected-access
        client.timeout = None
        self.assertEqual(b"", client._recv(None))  # pylint: disable=protected-access

    def test_serial_client_repr(self):
        """Test serial client."""
        client = ModbusSerialClient()
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} socket={client.socket}, "
            f"method={client.method}, timeout={client.timeout}>"
        )
        self.assertEqual(repr(client), rep)


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
