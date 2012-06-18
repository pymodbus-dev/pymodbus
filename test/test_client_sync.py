#!/usr/bin/env python
import unittest
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
class mockTransaction(object):
    def execute(self, request): return True

class mockSocket(object):
    def close(self): return True
    def recv(self, size): return '\x00'*size
    def read(self, size): return '\x00'*size
    def send(self, msg): return len(msg)
    def write(self, msg): return len(msg)
    def recvfrom(self, size): return '\x00'*size
    def sendto(self, msg, *args): return len(msg)

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#
class SynchronousClientTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.client.sync module
    '''

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        '''
        Initializes the test environment
        '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

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
        client.transaction = mockTransaction()
        self.assertTrue(client.execute())

        # a successful connect, no transaction
        client.connect = lambda: True
        client.transaction = None
        self.assertEqual(client.__enter__(), client)
        self.assertRaises(ConnectionException, lambda: client.execute())

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

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
