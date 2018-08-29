#!/usr/bin/env python
import unittest
from pymodbus.compat import IS_PYTHON3

if IS_PYTHON3:  # Python 3
    from unittest.mock import patch, Mock, MagicMock
else:  # Python 2
    from mock import patch, Mock, MagicMock
import socket
import serial

from pymodbus.client.sync import ModbusTcpClient, ModbusUdpClient
from pymodbus.client.sync import ModbusSerialClient, BaseModbusClient
from pymodbus.exceptions import ConnectionException, NotImplementedException
from pymodbus.exceptions import ParameterException
from pymodbus.transaction import ModbusAsciiFramer, ModbusRtuFramer
from pymodbus.transaction import ModbusBinaryFramer


# ---------------------------------------------------------------------------#
# Mock Classes
# ---------------------------------------------------------------------------#
class mockSocket(object):
    timeout = 2
    def close(self): return True

    def recv(self, size): return b'\x00' * size

    def read(self, size): return b'\x00' * size

    def send(self, msg): return len(msg)

    def write(self, msg): return len(msg)

    def recvfrom(self, size): return [b'\x00' * size]

    def sendto(self, msg, *args): return len(msg)

    def setblocking(self, flag): return None

    def in_waiting(self): return None



# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#
class SynchronousClientTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.client.sync module
    '''

    # -----------------------------------------------------------------------#
    # Test Base Client
    # -----------------------------------------------------------------------#

    def testBaseModbusClient(self):
        ''' Test the base class for all the clients '''

        client = BaseModbusClient(None)
        client.transaction = None
        self.assertRaises(NotImplementedException, lambda: client.connect())
        self.assertRaises(NotImplementedException, lambda: client._send(None))
        self.assertRaises(NotImplementedException, lambda: client._recv(None))
        self.assertRaises(NotImplementedException, lambda: client.__enter__())
        self.assertRaises(NotImplementedException, lambda: client.execute())
        self.assertRaises(NotImplementedException, lambda: client.is_socket_open())
        self.assertEqual("Null Transport", str(client))
        client.close()
        client.__exit__(0, 0, 0)

        # a successful execute
        client.connect = lambda: True
        client.transaction = Mock(**{'execute.return_value': True})
        self.assertEqual(client, client.__enter__())
        self.assertTrue(client.execute())

        # a unsuccessful connect
        client.connect = lambda: False
        self.assertRaises(ConnectionException, lambda: client.__enter__())
        self.assertRaises(ConnectionException, lambda: client.execute())

    # -----------------------------------------------------------------------#
    # Test UDP Client
    # -----------------------------------------------------------------------#

    def testSyncUdpClientInstantiation(self):
        client = ModbusUdpClient()
        self.assertNotEqual(client, None)

    def testBasicSyncUdpClient(self):
        ''' Test the basic methods for the udp sync client'''

        # receive/send
        client = ModbusUdpClient()
        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))
        self.assertEqual(1, client._send(b'\x00'))
        self.assertEqual(b'\x00', client._recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("ModbusUdpClient(127.0.0.1:502)", str(client))

    def testUdpClientAddressFamily(self):
        ''' Test the Udp client get address family method'''
        client = ModbusUdpClient()
        self.assertEqual(socket.AF_INET,
                         client._get_address_family('127.0.0.1'))
        self.assertEqual(socket.AF_INET6, client._get_address_family('::1'))

    def testUdpClientConnect(self):
        ''' Test the Udp client connection method'''
        with patch.object(socket, 'socket') as mock_method:
            class DummySocket(object):
                def settimeout(self, *a, **kwa):
                    pass

            mock_method.return_value = DummySocket()
            client = ModbusUdpClient()
            self.assertTrue(client.connect())

        with patch.object(socket, 'socket') as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusUdpClient()
            self.assertFalse(client.connect())

    def testUdpClientSend(self):
        ''' Test the udp client send method'''
        client = ModbusUdpClient()
        self.assertRaises(ConnectionException, lambda: client._send(None))

        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))
        self.assertEqual(4, client._send('1234'))

    def testUdpClientRecv(self):
        ''' Test the udp client receive method'''
        client = ModbusUdpClient()
        self.assertRaises(ConnectionException, lambda: client._recv(1024))

        client.socket = mockSocket()
        self.assertEqual(b'', client._recv(0))
        self.assertEqual(b'\x00' * 4, client._recv(4))

    def testUdpClientRepr(self):
        client = ModbusUdpClient()
        rep = "<{} at {} socket={}, ipaddr={}, port={}, timeout={}>".format(
            client.__class__.__name__, hex(id(client)), client.socket,
            client.host, client.port, client.timeout
        )
        self.assertEqual(repr(client), rep)


    # -----------------------------------------------------------------------#
    # Test TCP Client
    # -----------------------------------------------------------------------#

    def testSyncTcpClientInstantiation(self):
        client = ModbusTcpClient()
        self.assertNotEqual(client, None)

    @patch('pymodbus.client.sync.select')
    def testBasicSyncTcpClient(self, mock_select):
        ''' Test the basic methods for the tcp sync client'''

        # receive/send
        mock_select.select.return_value = [True]
        client = ModbusTcpClient()
        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))
        self.assertEqual(1, client._send(b'\x00'))
        self.assertEqual(b'\x00', client._recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("ModbusTcpClient(127.0.0.1:502)", str(client))

    def testTcpClientConnect(self):
        ''' Test the tcp client connection method'''
        with patch.object(socket, 'create_connection') as mock_method:
            mock_method.return_value = object()
            client = ModbusTcpClient()
            self.assertTrue(client.connect())

        with patch.object(socket, 'create_connection') as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusTcpClient()
            self.assertFalse(client.connect())

    def testTcpClientSend(self):
        ''' Test the tcp client send method'''
        client = ModbusTcpClient()
        self.assertRaises(ConnectionException, lambda: client._send(None))

        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))
        self.assertEqual(4, client._send('1234'))

    @patch('pymodbus.client.sync.select')
    def testTcpClientRecv(self, mock_select):
        ''' Test the tcp client receive method'''

        mock_select.select.return_value = [True]
        client = ModbusTcpClient()
        self.assertRaises(ConnectionException, lambda: client._recv(1024))

        client.socket = mockSocket()
        self.assertEqual(b'', client._recv(0))
        self.assertEqual(b'\x00' * 4, client._recv(4))

        mock_socket = MagicMock()
        mock_socket.recv.side_effect = iter([b'\x00', b'\x01', b'\x02'])
        client.socket = mock_socket
        client.timeout = 1
        self.assertEqual(b'\x00\x01\x02', client._recv(3))
        mock_socket.recv.side_effect = iter([b'\x00', b'\x01', b'\x02'])
        self.assertEqual(b'\x00\x01', client._recv(2))
        mock_select.select.return_value = [False]
        self.assertEqual(b'', client._recv(2))
        client.socket = mockSocket()
        mock_select.select.return_value = [True]
        self.assertIn(b'\x00', client._recv(None))

    def testSerialClientRpr(self):
        client = ModbusTcpClient()
        rep = "<{} at {} socket={}, ipaddr={}, port={}, timeout={}>".format(
            client.__class__.__name__, hex(id(client)), client.socket,
            client.host, client.port, client.timeout
        )
        self.assertEqual(repr(client), rep)
    # -----------------------------------------------------------------------#
    # Test Serial Client
    # -----------------------------------------------------------------------#

    def testSyncSerialClientInstantiation(self):
        client = ModbusSerialClient()
        self.assertNotEqual(client, None)
        self.assertTrue(isinstance(ModbusSerialClient(method='ascii').framer,
                                   ModbusAsciiFramer))
        self.assertTrue(isinstance(ModbusSerialClient(method='rtu').framer,
                                   ModbusRtuFramer))
        self.assertTrue(isinstance(ModbusSerialClient(method='binary').framer,
                                   ModbusBinaryFramer))
        self.assertRaises(ParameterException,
                          lambda: ModbusSerialClient(method='something'))

    def testSyncSerialRTUClientTimeouts(self):
        client = ModbusSerialClient(method="rtu", baudrate=9600)
        assert client.silent_interval == round((3.5 * 11 / 9600), 6)
        client = ModbusSerialClient(method="rtu", baudrate=38400)
        assert client.silent_interval == round((1.75 / 1000), 6)

    @patch("serial.Serial")
    def testBasicSyncSerialClient(self, mock_serial):
        ''' Test the basic methods for the serial sync client'''

        # receive/send
        mock_serial.in_waiting = 0
        mock_serial.write = lambda x: len(x)

        mock_serial.read = lambda size: b'\x00' * size
        client = ModbusSerialClient()
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client._send(None))
        client.state = 0
        self.assertEqual(1, client._send(b'\x00'))
        self.assertEqual(b'\x00', client._recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual('ModbusSerialClient(ascii baud[19200])', str(client))

    def testSerialClientConnect(self):
        ''' Test the serial client connection method'''
        with patch.object(serial, 'Serial') as mock_method:
            mock_method.return_value = object()
            client = ModbusSerialClient()
            self.assertTrue(client.connect())

        with patch.object(serial, 'Serial') as mock_method:
            mock_method.side_effect = serial.SerialException()
            client = ModbusSerialClient()
            self.assertFalse(client.connect())

    @patch("serial.Serial")
    def testSerialClientSend(self, mock_serial):
        ''' Test the serial client send method'''
        mock_serial.in_waiting = None
        mock_serial.write = lambda x: len(x)
        client = ModbusSerialClient()
        self.assertRaises(ConnectionException, lambda: client._send(None))
        # client.connect()
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client._send(None))
        client.state = 0
        self.assertEqual(4, client._send('1234'))

    @patch("serial.Serial")
    def testSerialClientCleanupBufferBeforeSend(self, mock_serial):
        ''' Test the serial client send method'''
        mock_serial.in_waiting = 4
        mock_serial.read = lambda x: b'1' * x
        mock_serial.write = lambda x: len(x)
        client = ModbusSerialClient()
        self.assertRaises(ConnectionException, lambda: client._send(None))
        # client.connect()
        client.socket = mock_serial
        client.state = 0
        self.assertEqual(0, client._send(None))
        client.state = 0
        self.assertEqual(4, client._send('1234'))

    def testSerialClientRecv(self):
        ''' Test the serial client receive method'''
        client = ModbusSerialClient()
        self.assertRaises(ConnectionException, lambda: client._recv(1024))

        client.socket = mockSocket()
        self.assertEqual(b'', client._recv(0))
        self.assertEqual(b'\x00' * 4, client._recv(4))
        client.socket = MagicMock()
        client.socket.read.return_value = b''
        self.assertEqual(b'', client._recv(None))
        client.socket.timeout = 0
        self.assertEqual(b'', client._recv(0))

    def testSerialClientRepr(self):
        client = ModbusSerialClient()
        rep = "<{} at {} socket={}, method={}, timeout={}>".format(
            client.__class__.__name__, hex(id(client)), client.socket,
            client.method, client.timeout
        )
        self.assertEqual(repr(client), rep)
# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
