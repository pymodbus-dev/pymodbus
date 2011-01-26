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
        event.decode('\x00\x70')
        self.assertTrue(event.overrun)
        self.assertTrue(event.listen)
        self.assertTrue(event.broadcast)

    def testRemoteSentEvent(self):
        event = RemoteSendEvent()
        result = event.encode()
        self.assertEqual(result, '\x40')
        event.decode('\x00\x70')
        self.assertTrue(event.read)
        self.assertTrue(event.slave_abort)
        self.assertTrue(event.slave_busy)
        self.assertTrue(event.slave_nak)
        self.assertTrue(event.write_timeout)
        self.assertTrue(event.listen)

    def testEnteredListenModeEvent(self):
        event = EnteredListenModeEvent()
        result = event.encode()
        self.assertEqual(result, '\x04')
        event.decode('\x04')
        self.assertEqual(event.value, 0x04)
        self.assertRaises(ParameterException, lambda: event.decode('\x00'))

    def testCommunicationRestartEvent(self):
        event = CommunicationRestartEvent()
        result = event.encode()
        self.assertEqual(result, '\x00')
        event.decode('\x00')
        self.assertEqual(event.value, 0x00)
        self.assertRaises(ParameterException, lambda: event.decode('\x04'))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
