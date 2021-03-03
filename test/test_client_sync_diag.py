#!/usr/bin/env python
import unittest
from itertools import count
from pymodbus.compat import IS_PYTHON3

if IS_PYTHON3:  # Python 3
    from unittest.mock import patch, Mock, MagicMock
else:  # Python 2
    from mock import patch, Mock, MagicMock
import socket

from pymodbus.client.sync_diag import ModbusTcpDiagClient, get_client
from pymodbus.exceptions import ConnectionException, NotImplementedException
from pymodbus.exceptions import ParameterException
from test.test_client_sync import mockSocket


# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#
class SynchronousDiagnosticClientTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.client.sync_diag module. It is
    a copy of parts of the test for the TCP class in the pymodbus.client.sync
    module, as it should operate identically and only log some additional
    lines.
    '''

    # -----------------------------------------------------------------------#
    # Test TCP Diagnostic Client
    # -----------------------------------------------------------------------#

    def testSyncTcpDiagClientInstantiation(self):
        client = get_client()
        self.assertNotEqual(client, None)

    def testBasicSyncTcpDiagClient(self):
        ''' Test the basic methods for the tcp sync diag client'''

        # connect/disconnect
        client = ModbusTcpDiagClient()
        client.socket = mockSocket()
        self.assertTrue(client.connect())
        client.close()

    def testTcpDiagClientConnect(self):
        ''' Test the tcp sync diag client connection method'''
        with patch.object(socket, 'create_connection') as mock_method:
            mock_method.return_value = object()
            client = ModbusTcpDiagClient()
            self.assertTrue(client.connect())

        with patch.object(socket, 'create_connection') as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusTcpDiagClient()
            self.assertFalse(client.connect())

    @patch('pymodbus.client.sync.time')
    @patch('pymodbus.client.sync_diag.time')
    @patch('pymodbus.client.sync.select')
    def testTcpDiagClientRecv(self, mock_select, mock_diag_time, mock_time):
        ''' Test the tcp sync diag client receive method'''

        mock_select.select.return_value = [True]
        mock_time.time.side_effect = count()
        mock_diag_time.time.side_effect = count()
        client = ModbusTcpDiagClient()
        self.assertRaises(ConnectionException, lambda: client._recv(1024))

        client.socket = mockSocket()
        # Test logging of non-delayed responses
        self.assertIn(b'\x00', client._recv(None))
        self.assertEqual(b'\x00', client._recv(1))

        # Fool diagnostic logger into thinking we're running late,
        # test logging of delayed responses
        mock_diag_time.time.side_effect = count(step=3)
        self.assertEqual(b'', client._recv(0))
        self.assertEqual(b'\x00' * 4, client._recv(4))

        mock_socket = MagicMock()
        mock_socket.recv.side_effect = iter([b'\x00', b'\x01', b'\x02'])
        client.socket = mock_socket
        client.timeout = 3
        self.assertEqual(b'\x00\x01\x02', client._recv(3))
        mock_socket.recv.side_effect = iter([b'\x00', b'\x01', b'\x02'])
        self.assertEqual(b'\x00\x01', client._recv(2))
        mock_select.select.return_value = [False]
        self.assertEqual(b'', client._recv(2))
        client.socket = mockSocket()
        mock_select.select.return_value = [True]
        self.assertIn(b'\x00', client._recv(None))

        mock_socket = MagicMock()
        mock_socket.recv.return_value = b''
        client.socket = mock_socket
        self.assertRaises(ConnectionException, lambda: client._recv(1024))

        mock_socket.recv.side_effect = iter([b'\x00', b'\x01', b'\x02', b''])
        client.socket = mock_socket
        self.assertEqual(b'\x00\x01\x02', client._recv(1024))

    def testTcpDiagClientRpr(self):
        client = ModbusTcpDiagClient()
        rep = "<{} at {} socket={}, ipaddr={}, port={}, timeout={}>".format(
            client.__class__.__name__, hex(id(client)), client.socket,
            client.host, client.port, client.timeout
        )
        self.assertEqual(repr(client), rep)


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
