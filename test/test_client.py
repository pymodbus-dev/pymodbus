#!/usr/bin/env python
import unittest
from twisted.test import test_protocols
from pymodbus.client.sync import ModbusTcpClient, ModbusUdpClient
from pymodbus.client.sync import ModbusSerialClient

class SynchronousClientTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.client.sync module
    '''

    def setUp(self):
        pass

    def testSyncUdpClientInstantiation(self):
        client = ModbusUdpClient()
        self.assertNotEqual(client, None)
    
    def testSyncTcpClientInstantiation(self):
        client = ModbusTcpClient()
        self.assertNotEqual(client, None)
    
    def testSyncSerialClientInstantiation(self):
        client = ModbusSerialClient
        self.assertNotEqual(client, None)
