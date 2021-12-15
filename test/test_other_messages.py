#!/usr/bin/env python
import unittest
from pymodbus.other_message import *
import mock


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
        request.decode(b'\x12')
        self.assertEqual(request.encode(), b'')
        self.assertEqual(request.execute().function_code, 0x07)

        response = ReadExceptionStatusResponse(0x12)
        self.assertEqual(response.encode(), b'\x12')
        response.decode(b'\x12')
        self.assertEqual(response.status, 0x12)

    def testGetCommEventCounter(self):
        request = GetCommEventCounterRequest()
        request.decode(b'\x12')
        self.assertEqual(request.encode(), b'')
        self.assertEqual(request.execute().function_code, 0x0b)

        response = GetCommEventCounterResponse(0x12)
        self.assertEqual(response.encode(), b'\x00\x00\x00\x12')
        response.decode(b'\x00\x00\x00\x12')
        self.assertEqual(response.status, True)
        self.assertEqual(response.count, 0x12)

        response.status = False
        self.assertEqual(response.encode(), b'\xFF\xFF\x00\x12')

    def testGetCommEventLog(self):
        request = GetCommEventLogRequest()
        request.decode(b'\x12')
        self.assertEqual(request.encode(), b'')
        self.assertEqual(request.execute().function_code, 0x0c)

        response = GetCommEventLogResponse()
        self.assertEqual(response.encode(), b'\x06\x00\x00\x00\x00\x00\x00')
        response.decode(b'\x06\x00\x00\x00\x12\x00\x12')
        self.assertEqual(response.status, True)
        self.assertEqual(response.message_count, 0x12)
        self.assertEqual(response.event_count, 0x12)
        self.assertEqual(response.events, [])

        response.status = False
        self.assertEqual(response.encode(), b'\x06\xff\xff\x00\x12\x00\x12')

    def testGetCommEventLogWithEvents(self):
        response = GetCommEventLogResponse(events=[0x12,0x34,0x56])
        self.assertEqual(response.encode(), b'\x09\x00\x00\x00\x00\x00\x00\x12\x34\x56')
        response.decode(b'\x09\x00\x00\x00\x12\x00\x12\x12\x34\x56')
        self.assertEqual(response.status, True)
        self.assertEqual(response.message_count, 0x12)
        self.assertEqual(response.event_count, 0x12)
        self.assertEqual(response.events, [0x12,0x34,0x56])

    def testReportSlaveIdRequest(self):
        with mock.patch("pymodbus.other_message.DeviceInformationFactory") as dif:
            # First test regular identity strings
            identity = {
                0x00: 'VN',  # VendorName
                0x01: 'PC',  # ProductCode
                0x02: 'REV',  # MajorMinorRevision
                0x03: 'VU',  # VendorUrl
                0x04: 'PN',  # ProductName
                0x05: 'MN',  # ModelName
                0x06: 'UAN',  # UserApplicationName
                0x07: 'RA',  # reserved
                0x08: 'RB',  # reserved
            }
            dif.get.return_value = identity
            expected_identity = "-".join(identity.values()).encode()

            request = ReportSlaveIdRequest()
            response = request.execute()
            self.assertEqual(response.identifier, expected_identity)

            # Change to byte strings and test again (final result should be the same)
            identity = {
                0x00: b'VN',  # VendorName
                0x01: b'PC',  # ProductCode
                0x02: b'REV',  # MajorMinorRevision
                0x03: b'VU',  # VendorUrl
                0x04: b'PN',  # ProductName
                0x05: b'MN',  # ModelName
                0x06: b'UAN',  # UserApplicationName
                0x07: b'RA',  # reserved
                0x08: b'RB',  # reserved
            }
            dif.get.return_value = identity

            request = ReportSlaveIdRequest()
            response = request.execute()
            self.assertEqual(response.identifier, expected_identity)

    def testReportSlaveId(self):
        with mock.patch("pymodbus.other_message.DeviceInformationFactory") as dif:
            dif.get.return_value = dict()
            request = ReportSlaveIdRequest()
            request.decode(b'\x12')
            self.assertEqual(request.encode(), b'')
            self.assertEqual(request.execute().function_code, 0x11)

            response = ReportSlaveIdResponse(request.execute().identifier, True)

            self.assertEqual(response.encode(), b'\tPymodbus\xff')
            response.decode(b'\x03\x12\x00')
            self.assertEqual(response.status, False)
            self.assertEqual(response.identifier, b'\x12\x00')

            response.status = False
            self.assertEqual(response.encode(), b'\x03\x12\x00\x00')

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
