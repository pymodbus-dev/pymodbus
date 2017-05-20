#!/usr/bin/env python
import unittest
from pymodbus.events import *
from pymodbus.exceptions import NotImplementedException
from pymodbus.exceptions import ParameterException

class ModbusEventsTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.device module
    '''

    def setUp(self):
        ''' Sets up the test environment '''
        pass

    def tearDown(self):
        ''' Cleans up the test environment '''
        pass

    def testModbusEventBaseClass(self):
        event = ModbusEvent()
        self.assertRaises(NotImplementedException, event.encode)
        self.assertRaises(NotImplementedException, lambda: event.decode(None))

    def testRemoteReceiveEvent(self):
        event = RemoteReceiveEvent()
        event.decode(b'\x70')
        self.assertTrue(event.overrun)
        self.assertTrue(event.listen)
        self.assertTrue(event.broadcast)

    def testRemoteSentEvent(self):
        event = RemoteSendEvent()
        result = event.encode()
        self.assertEqual(result, b'\x40')
        event.decode(b'\x7f')
        self.assertTrue(event.read)
        self.assertTrue(event.slave_abort)
        self.assertTrue(event.slave_busy)
        self.assertTrue(event.slave_nak)
        self.assertTrue(event.write_timeout)
        self.assertTrue(event.listen)

    def testRemoteSentEventEncode(self):
        arguments = {
            'read'          : True,
            'slave_abort'   : True,
            'slave_busy'    : True,
            'slave_nak'     : True,
            'write_timeout' : True,
            'listen'        : True,
        }
        event = RemoteSendEvent(**arguments)
        result = event.encode()
        self.assertEqual(result, b'\x7f')

    def testEnteredListenModeEvent(self):
        event = EnteredListenModeEvent()
        result = event.encode()
        self.assertEqual(result, b'\x04')
        event.decode(b'\x04')
        self.assertEqual(event.value, 0x04)
        self.assertRaises(ParameterException, lambda: event.decode(b'\x00'))

    def testCommunicationRestartEvent(self):
        event = CommunicationRestartEvent()
        result = event.encode()
        self.assertEqual(result, b'\x00')
        event.decode(b'\x00')
        self.assertEqual(event.value, 0x00)
        self.assertRaises(ParameterException, lambda: event.decode(b'\x04'))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
