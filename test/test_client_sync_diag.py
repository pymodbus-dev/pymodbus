"""Test client sync diag."""
import socket
from itertools import count
from test import mock
from test.test_client_sync import mockSocket

import pytest

from pymodbus.client.sync_diag import ModbusTcpDiagClient, get_client
from pymodbus.exceptions import ConnectionException


# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


class TestSynchronousDiagnosticClient:
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
        assert client

    def test_basic_syn_tcp_diag_client(self):
        """Test the basic methods for the tcp sync diag client"""
        # connect/disconnect
        client = ModbusTcpDiagClient()
        client.socket = mockSocket()
        assert client.connect()
        client.close()

    def test_tcp_diag_client_connect(self):
        """Test the tcp sync diag client connection method"""
        with mock.patch.object(socket, "create_connection") as mock_method:
            mock_method.return_value = object()
            client = ModbusTcpDiagClient()
            assert client.connect()

        with mock.patch.object(socket, "create_connection") as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusTcpDiagClient()
            assert not client.connect()

    @mock.patch("pymodbus.client.tcp.time")
    @mock.patch("pymodbus.client.sync_diag.time")
    @mock.patch("pymodbus.client.tcp.select")
    def test_tcp_diag_client_recv(self, mock_select, mock_diag_time, mock_time):
        """Test the tcp sync diag client receive method"""
        mock_select.select.return_value = [True]
        mock_time.time.side_effect = count()
        mock_diag_time.time.side_effect = count()
        client = ModbusTcpDiagClient()
        with pytest.raises(ConnectionException):
            client.recv(1024)
        client.socket = mockSocket()
        # Test logging of non-delayed responses
        client.socket.mock_store(b"\x00")
        assert b"\x00" in client.recv(None)
        client.socket = mockSocket()
        client.socket.mock_store(b"\x00")
        assert client.recv(1) == b"\x00"

        # Fool diagnostic logger into thinking we"re running late,
        # test logging of delayed responses
        mock_diag_time.time.side_effect = count(step=3)
        client.socket.mock_store(b"\x00" * 4)
        assert client.recv(4) == b"\x00" * 4
        assert client.recv(0) == b""

        client.socket.mock_store(b"\x00\x01\x02")
        client.timeout = 3
        assert client.recv(3) == b"\x00\x01\x02"
        client.socket.mock_store(b"\x00\x01\x02")
        assert client.recv(2) == b"\x00\x01"
        mock_select.select.return_value = [False]
        assert client.recv(2) == b""
        client.socket = mockSocket()
        client.socket.mock_store(b"\x00")
        mock_select.select.return_value = [True]
        assert b"\x00" in client.recv(None)

        mock_socket = mock.MagicMock()
        client.socket = mock_socket
        mock_socket.recv.return_value = b""
        with pytest.raises(ConnectionException):
            client.recv(1024)
        client.socket = mockSocket()
        client.socket.mock_store(b"\x00\x01\x02")
        assert client.recv(1024) == b"\x00\x01\x02"

    def test_tcp_diag_client_repr(self):
        """Test tcp diag client."""
        client = ModbusTcpDiagClient()
        rep = (
            f"<{client.__class__.__name__} at {hex(id(client))} "
            f"socket={client.socket}, ipaddr={client.params.host}, "
            f"port={client.params.port}, timeout={client.params.timeout}>"
        )
        assert repr(client) == rep
