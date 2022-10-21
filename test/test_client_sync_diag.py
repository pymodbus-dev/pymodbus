"""Test client sync diag."""
import socket
import unittest
from itertools import count
from test.test_client_sync import mockSocket
from unittest.mock import MagicMock, patch

from pymodbus.client.sync_diag import ModbusTcpDiagClient, get_client
from pymodbus.exceptions import ConnectionException


# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


class SynchronousDiagnosticClientTest(unittest.TestCase):
    """Unittest for the pymodbus.client.sync_diag module.

    It is a copy of parts of the test for the TCP class in the pymodbus.client
    module, as it should operate identically and only log some additional
    lines.
    """

    # -----------------------------------------------------------------------#
    # Test TCP Diagnostic Client
    # -----------------------------------------------------------------------#

    def test_syn_tcp_diag_client_instantiation(self):
        """Test sync tcp diag client."""
        client = get_client()
        self.assertNotEqual(client, None)

    def test_basic_syn_tcp_diag_client(self):
        """Test the basic methods for the tcp sync diag client"""
        # connect/disconnect
        client = ModbusTcpDiagClient()
        client.socket = mockSocket()
        self.assertTrue(client.connect())
        client.close()

    def test_tcp_diag_client_connect(self):
        """Test the tcp sync diag client connection method"""
        with patch.object(socket, "create_connection") as mock_method:
            mock_method.return_value = object()
            client = ModbusTcpDiagClient()
            self.assertTrue(client.connect())

        with patch.object(socket, "create_connection") as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusTcpDiagClient()
            self.assertFalse(client.connect())

    @patch("pymodbus.client.tcp.time")
    @patch("pymodbus.client.sync_diag.time")
    @patch("pymodbus.client.tcp.select")
    def test_tcp_diag_client_recv(self, mock_select, mock_diag_time, mock_time):
        """Test the tcp sync diag client receive method"""
        mock_select.select.return_value = [True]
        mock_time.time.side_effect = count()
        mock_diag_time.time.side_effect = count()
        client = ModbusTcpDiagClient()
        self.assertRaises(
            ConnectionException,
            lambda: client.recv(1024),
        )

        client.socket = mockSocket()
        # Test logging of non-delayed responses
        client.socket.mock_store(b"\x00")
        self.assertIn(b"\x00", client.recv(None))
        client.socket = mockSocket()
        client.socket.mock_store(b"\x00")
        self.assertEqual(b"\x00", client.recv(1))

        # Fool diagnostic logger into thinking we"re running late,
        # test logging of delayed responses
        mock_diag_time.time.side_effect = count(step=3)
        client.socket.mock_store(b"\x00" * 4)
        self.assertEqual(b"\x00" * 4, client.recv(4))
        self.assertEqual(b"", client.recv(0))

        client.socket.mock_store(b"\x00\x01\x02")
        client.timeout = 3
        self.assertEqual(b"\x00\x01\x02", client.recv(3))
        client.socket.mock_store(b"\x00\x01\x02")
        self.assertEqual(b"\x00\x01", client.recv(2))
        mock_select.select.return_value = [False]
        self.assertEqual(b"", client.recv(2))
        client.socket = mockSocket()
        client.socket.mock_store(b"\x00")
        mock_select.select.return_value = [True]
        self.assertIn(b"\x00", client.recv(None))

        mock_socket = MagicMock()
        client.socket = mock_socket
        mock_socket.recv.return_value = b""
        self.assertRaises(
            ConnectionException,
            lambda: client.recv(1024),
        )
        client.socket = mockSocket()
        client.socket.mock_store(b"\x00\x01\x02")
        self.assertEqual(b"\x00\x01\x02", client.recv(1024))

    def test_tcp_diag_client_repr(self):
        """Test tcp diag client."""
        client = ModbusTcpDiagClient()
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} "
            f"socket={client.socket}, ipaddr={client.params.host}, "
            f"port={client.params.port}, timeout={client.params.timeout}>"
        )
        self.assertEqual(repr(client), rep)
