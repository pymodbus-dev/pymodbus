'''
I'm not sure how wel this will work as we have the client try and run
as many request as it can as fast as it can without stopping, and then
finishing...hmmmm
'''
from twisted.trial import unittest
from twisted.test import test_protocols
from pymodbus.client.async import ModbusClientFactory
from pymodbus.mexceptions import *
from pymodbus.bit_read_message import ReadCoilsRequest

class SimpleDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.client module
    '''

    def setUp(self):
        self.t = test_protocols.StringIOWithoutClosing()
        self.requests = [
                ReadCoilsRequest(1, 16),
                ReadCoilsRequest(17,16),
                ReadCoilsRequest(0,99),
        ]
        self.f = ModbusClientFactory(self.requests)

    def testReadRequest(self):
        pass
        #self.p.dataReceived("moshez\r\n")
        #self.failUnlessEqual(self.t.getvalue(), "Login: moshez\nNo such user\n")

    def testWriteRequest(self):
        pass
        #self.p.dataReceived("moshez\r\n")
        #self.failUnlessEqual(self.t.getvalue(), "Login: moshez\nNo such user\n")
