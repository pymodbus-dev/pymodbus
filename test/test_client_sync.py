#!/usr/bin/env python
import unittest
import socket
import serial
from mock import patch, Mock
from twisted.test import test_protocols
from pymodbus.client.sync import ModbusTcpClient, ModbusUdpClient
from pymodbus.client.sync import ModbusSerialClient, BaseModbusClient
from pymodbus.exceptions import ConnectionException, NotImplementedException
from pymodbus.exceptions import ParameterException
from pymodbus.transaction import ModbusAsciiFramer, ModbusRtuFramer
from pymodbus.transaction import ModbusBinaryFramer

#---------------------------------------------------------------------------#
# Mock Classes
#---------------------------------------------------------------------------#
class mockSocket(object):
    def close(self): return True
    def recv(self, size): return '\x00'*size
    def read(self, size): return '\x00'*size
    def send(self, msg): return len(msg)
    def write(self, msg): return len(msg)
    def recvfrom(self, size): return ['\x00'*size]
    def sendto(self, msg, *args): return len(msg)

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class SynchronousClientTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.client.sync module
    '''

    #-----------------------------------------------------------------------#
    # Test Base Client
    #-----------------------------------------------------------------------#

    def testBaseModbusClient(self):
        ''' Test the base class for all the clients '''

        client = BaseModbusClient(None)
        client.transaction = None
        self.assertRaises(NotImplementedException, lambda: client.connect())
        self.assertRaises(NotImplementedException, lambda: client._send(None))
        self.assertRaises(NotImplementedException, lambda: client._recv(None))
        self.assertRaises(NotImplementedException, lambda: client.__enter__())
        self.assertRaises(NotImplementedException, lambda: client.execute())
        self.assertEquals("Null Transport", str(client))
        client.close()
        client.__exit__(0,0,0)

        # a successful execute
        client.connect = lambda: True
        client.transaction = Mock(**{'execute.return_value': True})
        self.assertEqual(client, client.__enter__())
        self.assertTrue(client.execute())

        # a unsuccessful connect
        client.connect = lambda: False
        self.assertRaises(ConnectionException, lambda: client.__enter__())
        self.assertRaises(ConnectionException, lambda: client.execute())

    #-----------------------------------------------------------------------#
    # Test UDP Client
    #-----------------------------------------------------------------------#

    def testSyncUdpClientInstantiation(self):
        client = ModbusUdpClient()
        self.assertNotEqual(client, None)

    def testBasicSyncUdpClient(self):
        ''' Test the basic methods for the udp sync client'''

        # receive/send
        client = ModbusUdpClient()
        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))
        self.assertEqual(1, client._send('\x00'))
        self.assertEqual('\x00', client._recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("127.0.0.1:502", str(client))

    def testUdpClientAddressFamily(self):
        ''' Test the Udp client get address family method'''
        client = ModbusUdpClient()
        self.assertEqual(socket.AF_INET, client._get_address_family('127.0.0.1'))
        self.assertEqual(socket.AF_INET6, client._get_address_family('::1'))

    def testUdpClientConnect(self):
        ''' Test the Udp client connection method'''
        with patch.object(socket, 'socket') as mock_method:
            mock_method.return_value = object()
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
        self.assertEqual('', client._recv(0))
        self.assertEqual('\x00'*4, client._recv(4))

    #-----------------------------------------------------------------------#
    # Test TCP Client
    #-----------------------------------------------------------------------#
    
    def testSyncTcpClientInstantiation(self):
        client = ModbusTcpClient()
        self.assertNotEqual(client, None)

    def testBasicSyncTcpClient(self):
        ''' Test the basic methods for the tcp sync client'''

        # receive/send
        client = ModbusTcpClient()
        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))
        self.assertEqual(1, client._send('\x00'))
        self.assertEqual('\x00', client._recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("127.0.0.1:502", str(client))

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

    def testTcpClientRecv(self):
        ''' Test the tcp client receive method'''
        client = ModbusTcpClient()
        self.assertRaises(ConnectionException, lambda: client._recv(1024))

        client.socket = mockSocket()
        self.assertEqual('', client._recv(0))
        self.assertEqual('\x00'*4, client._recv(4))
    
    #-----------------------------------------------------------------------#
    # Test Serial Client
    #-----------------------------------------------------------------------#

    def testSyncSerialClientInstantiation(self):
        client = ModbusSerialClient()
        self.assertNotEqual(client, None)
        self.assertTrue(isinstance(ModbusSerialClient(method='ascii').framer, ModbusAsciiFramer))
        self.assertTrue(isinstance(ModbusSerialClient(method='rtu').framer, ModbusRtuFramer))
        self.assertTrue(isinstance(ModbusSerialClient(method='binary').framer, ModbusBinaryFramer))
        self.assertRaises(ParameterException, lambda: ModbusSerialClient(method='something'))

    def testBasicSyncSerialClient(self):
        ''' Test the basic methods for the serial sync client'''

        # receive/send
        client = ModbusSerialClient()
        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))
        self.assertEqual(1, client._send('\x00'))
        self.assertEqual('\x00', client._recv(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual('ascii baud[19200]', str(client))

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

    def testSerialClientSend(self):
        ''' Test the serial client send method'''
        client = ModbusSerialClient()
        self.assertRaises(ConnectionException, lambda: client._send(None))

        client.socket = mockSocket()
        self.assertEqual(0, client._send(None))
        self.assertEqual(4, client._send('1234'))

    def testSerialClientRecv(self):
        ''' Test the serial client receive method'''
        client = ModbusSerialClient()
        self.assertRaises(ConnectionException, lambda: client._recv(1024))

        client.socket = mockSocket()
        self.assertEqual('', client._recv(0))
        self.assertEqual('\x00'*4, client._recv(4))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
