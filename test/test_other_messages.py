#!/usr/bin/env python
import unittest
from pymodbus.other_message import *

class ModbusOtherMessageTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.other_message module
    '''

    def setUp(self):
        self.requests = [
            ReadExceptionStatusRequest,
            GetCommEventCounterRequest,
            GetCommEventLogRequest,
            ReportSlaveIdRequest,
        ]

        self.responses = [
            lambda: ReadExceptionStatusResponse(0x12),
            lambda: GetCommEventCounterResponse(0x12),
            GetCommEventLogResponse,
            lambda: ReportSlaveIdResponse(0x12),
        ]

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.requests
        del self.responses

    def testOtherMessagesToString(self):
        for message in self.requests:
            self.assertNotEqual(str(message()), None)
        for message in self.responses:
            self.assertNotEqual(str(message()), None)

    def testReadExceptionStatus(self):
        request = ReadExceptionStatusRequest()
        request.decode('\x12')
        self.assertEqual(request.encode(), '')
        self.assertEqual(request.execute().function_code, 0x07)

        response = ReadExceptionStatusResponse(0x12)
        self.assertEqual(response.encode(), '\x12')
        response.decode('\x12')
        self.assertEqual(response.status, 0x12)

    def testGetCommEventCounter(self):
        request = GetCommEventCounterRequest()
        request.decode('\x12')
        self.assertEqual(request.encode(), '')
        self.assertEqual(request.execute().function_code, 0x0b)

        response = GetCommEventCounterResponse(0x12)
        self.assertEqual(response.encode(), '\x00\x00\x00\x12')
        response.decode('\x00\x00\x00\x12')
        self.assertEqual(response.status, True)
        self.assertEqual(response.count, 0x12)

        response.status = False
        self.assertEqual(response.encode(), '\xFF\xFF\x00\x12')

    def testGetCommEventLog(self):
        request = GetCommEventLogRequest()
        request.decode('\x12')
        self.assertEqual(request.encode(), '')
        self.assertEqual(request.execute().function_code, 0x0c)

        response = GetCommEventLogResponse()
        self.assertEqual(response.encode(), '\x06\x00\x00\x00\x00\x00\x00')
        response.decode('\x06\x00\x00\x00\x12\x00\x12')
        self.assertEqual(response.status, True)
        self.assertEqual(response.message_count, 0x12)
        self.assertEqual(response.event_count, 0x12)
        self.assertEqual(response.events, [])

        response.status = False
        self.assertEqual(response.encode(), '\x06\xff\xff\x00\x12\x00\x12')

    def testGetCommEventLogWithEvents(self):
        response = GetCommEventLogResponse(events=[0x12,0x34,0x56])
        self.assertEqual(response.encode(), '\x09\x00\x00\x00\x00\x00\x00\x12\x34\x56')
        response.decode('\x09\x00\x00\x00\x12\x00\x12\x12\x34\x56')
        self.assertEqual(response.status, True)
        self.assertEqual(response.message_count, 0x12)
        self.assertEqual(response.event_count, 0x12)
        self.assertEqual(response.events, [0x12,0x34,0x56])

    def testReportSlaveId(self):
        request = ReportSlaveIdRequest()
        request.decode('\x12')
        self.assertEqual(request.encode(), '')
        self.assertEqual(request.execute().function_code, 0x11)

        response = ReportSlaveIdResponse(request.execute().identifier, True)
        self.assertEqual(response.encode(), '\x0apymodbus\xff')
        response.decode('\x03\x12\x00')
        self.assertEqual(response.status, False)
        self.assertEqual(response.identifier, '\x12\x00')

        response.status = False
        self.assertEqual(response.encode(), '\x04\x12\x00\x00')

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
