#!/usr/bin/env python3
"""Test client sync diag."""
import unittest
from itertools import count
from unittest.mock import patch, MagicMock
from test.test_client_sync import mockSocket
import socket

from pymodbus.client.sync_diag import ModbusTcpDiagClient, get_client
from pymodbus.exceptions import ConnectionException


# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#
class SynchronousDiagnosticClientTest(unittest.TestCase):
    """Unittest for the pymodbus.client.sync_diag module.

    It is a copy of parts of the test for the TCP class in the pymodbus.client.sync
    module, as it should operate identically and only log some additional
    lines.
    """

    # -----------------------------------------------------------------------#
    # Test TCP Diagnostic Client
    # -----------------------------------------------------------------------#

    def test_sync_tcp_diag_client_instantiation(self):
        """Test sync tcp diag client."""
        client = get_client()
        self.assertNotEqual(client, None)

    def test_basic_sync_tcp_diag_client(self):
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

    @patch("pymodbus.client.sync.time")
    @patch("pymodbus.client.sync_diag.time")
    @patch("pymodbus.client.sync.select")
    def test_tcp_diag_client_recv(self, mock_select, mock_diag_time, mock_time):
        """Test the tcp sync diag client receive method"""
        mock_select.select.return_value = [True]
        mock_time.time.side_effect = count()
        mock_diag_time.time.side_effect = count()
        client = ModbusTcpDiagClient()
        self.assertRaises(
            ConnectionException, lambda: client._recv(1024)  # pylint: disable=protected-access
        )

        client.socket = mockSocket()
        # Test logging of non-delayed responses
        self.assertIn(b"\x00", client._recv(None))  # pylint: disable=protected-access
        self.assertEqual(b"\x00", client._recv(1))  # pylint: disable=protected-access

        # Fool diagnostic logger into thinking we"re running late,
        # test logging of delayed responses
        mock_diag_time.time.side_effect = count(step=3)
        self.assertEqual(
            b"\x00" * 4, client._recv(4)  # pylint: disable=protected-access
        )
        self.assertEqual(b"", client._recv(0))  # pylint: disable=protected-access

        mock_socket = MagicMock()
        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02"])
        client.timeout = 3
        client.socket = mock_socket
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
        client.socket = mock_socket
        mock_socket.recv.return_value = b""
        self.assertRaises(
            ConnectionException, lambda: client._recv(1024)  # pylint: disable=protected-access
        )

        mock_socket.recv.side_effect = iter([b"\x00", b"\x01", b"\x02", b""])
        client.socket = mock_socket
        self.assertEqual(
            b"\x00\x01\x02", client._recv(1024)  # pylint: disable=protected-access
        )

    def test_tcp_diag_client_repr(self):
        """Test tcp diag client."""
        client = ModbusTcpDiagClient()
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} "
            f"socket={client.socket}, ipaddr={client.host}, "
            f"port={client.port}, timeout={client.timeout}>"
        )
        self.assertEqual(repr(client), rep)


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
