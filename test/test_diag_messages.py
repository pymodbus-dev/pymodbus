#!/usr/bin/env python
import unittest
from pymodbus.exceptions import *
from pymodbus.constants import ModbusPlusOperation
from pymodbus.diag_message import *
from pymodbus.diag_message import DiagnosticStatusRequest
from pymodbus.diag_message import DiagnosticStatusResponse
from pymodbus.diag_message import DiagnosticStatusSimpleRequest
from pymodbus.diag_message import DiagnosticStatusSimpleResponse

class SimpleDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymodbus.diag_message module
    '''

    def setUp(self):
        self.requests = [
            #(DiagnosticStatusRequest,                      '\x00\x00\x00\x00'),
            #(DiagnosticStatusSimpleRequest,                '\x00\x00\x00\x00'),
            (RestartCommunicationsOptionRequest,            '\x00\x01\x00\x00', '\x00\x01\xff\x00'),
            (ReturnDiagnosticRegisterRequest,               '\x00\x02\x00\x00', '\x00\x02\x00\x00'),
            (ChangeAsciiInputDelimiterRequest,              '\x00\x03\x00\x00', '\x00\x03\x00\x00'),
            (ForceListenOnlyModeRequest,                    '\x00\x04\x00\x00', '\x00\x04'),
            (ReturnQueryDataRequest,                        '\x00\x00\x00\x00', '\x00\x00\x00\x00'),
            (ClearCountersRequest,                          '\x00\x0a\x00\x00', '\x00\x0a\x00\x00'),
            (ReturnBusMessageCountRequest,                  '\x00\x0b\x00\x00', '\x00\x0b\x00\x00'),
            (ReturnBusCommunicationErrorCountRequest,       '\x00\x0c\x00\x00', '\x00\x0c\x00\x00'),
            (ReturnBusExceptionErrorCountRequest,           '\x00\x0d\x00\x00', '\x00\x0d\x00\x00'),
            (ReturnSlaveMessageCountRequest,                '\x00\x0e\x00\x00', '\x00\x0e\x00\x00'),
            (ReturnSlaveNoResponseCountRequest,             '\x00\x0f\x00\x00', '\x00\x0f\x00\x00'),
            (ReturnSlaveNAKCountRequest,                    '\x00\x10\x00\x00', '\x00\x10\x00\x00'),
            (ReturnSlaveBusyCountRequest,                   '\x00\x11\x00\x00', '\x00\x11\x00\x00'),
            (ReturnSlaveBusCharacterOverrunCountRequest,    '\x00\x12\x00\x00', '\x00\x12\x00\x00'),
            (ReturnIopOverrunCountRequest,                  '\x00\x13\x00\x00', '\x00\x13\x00\x00'),
            (ClearOverrunCountRequest,                      '\x00\x14\x00\x00', '\x00\x14\x00\x00'),
            (GetClearModbusPlusRequest,                     '\x00\x15\x00\x00', '\x00\x15' + '\x00\x00' * 55),
        ]

        self.responses = [
            #(DiagnosticStatusResponse,                     '\x00\x00\x00\x00'),
            #(DiagnosticStatusSimpleResponse,               '\x00\x00\x00\x00'),
            (ReturnQueryDataResponse,                      '\x00\x00\x00\x00'),
            (RestartCommunicationsOptionResponse,          '\x00\x01\x00\x00'),
            (ReturnDiagnosticRegisterResponse,             '\x00\x02\x00\x00'),
            (ChangeAsciiInputDelimiterResponse,            '\x00\x03\x00\x00'),
            (ForceListenOnlyModeResponse,                  '\x00\x04'),
            (ReturnQueryDataResponse,                      '\x00\x00\x00\x00'),
            (ClearCountersResponse,                        '\x00\x0a\x00\x00'),
            (ReturnBusMessageCountResponse,                '\x00\x0b\x00\x00'),
            (ReturnBusCommunicationErrorCountResponse,     '\x00\x0c\x00\x00'),
            (ReturnBusExceptionErrorCountResponse,         '\x00\x0d\x00\x00'),
            (ReturnSlaveMessageCountResponse,              '\x00\x0e\x00\x00'),
            (ReturnSlaveNoReponseCountResponse,            '\x00\x0f\x00\x00'),
            (ReturnSlaveNAKCountResponse,                  '\x00\x10\x00\x00'),
            (ReturnSlaveBusyCountResponse,                 '\x00\x11\x00\x00'),
            (ReturnSlaveBusCharacterOverrunCountResponse,  '\x00\x12\x00\x00'),
            (ReturnIopOverrunCountResponse,                '\x00\x13\x00\x00'),
            (ClearOverrunCountResponse,                    '\x00\x14\x00\x00'),
            (GetClearModbusPlusResponse,                   '\x00\x15' + '\x00\x00' * 55),
        ]

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.requests
        del self.responses

    def testDiagnosticRequestsDecode(self):
        ''' Testing diagnostic request messages encoding '''
        for msg,enc,exe in self.requests:
            handle = DiagnosticStatusRequest()
            handle.decode(enc)
            self.assertEqual(handle.sub_function_code, msg.sub_function_code)

    def testDiagnosticSimpleRequests(self):
        ''' Testing diagnostic request messages encoding '''
        request = DiagnosticStatusSimpleRequest('\x12\x34')
        request.sub_function_code = 0x1234
        self.assertRaises(NotImplementedException, lambda: request.execute())
        self.assertEqual(request.encode(), '\x12\x34\x12\x34')

        response = DiagnosticStatusSimpleResponse(None)

    def testDiagnosticResponseDecode(self):
        ''' Testing diagnostic request messages encoding '''
        for msg,enc,exe in self.requests:
            handle = DiagnosticStatusResponse()
            handle.decode(enc)
            self.assertEqual(handle.sub_function_code, msg.sub_function_code)

    def testDiagnosticRequestsEncode(self):
        ''' Testing diagnostic request messages encoding '''
        for msg,enc,exe in self.requests:
            self.assertEqual(msg().encode(), enc)

    #def testDiagnosticResponse(self):
    #    ''' Testing diagnostic request messages '''
    #    for msg,enc in self.responses:
    #        self.assertEqual(msg().encode(), enc)

    def testDiagnosticExecute(self):
        ''' Testing diagnostic message execution '''
        for msg,enc,exe in self.requests:
            self.assertEqual(msg().execute().encode(), exe)

    def testReturnQueryDataRequest(self):
        ''' Testing diagnostic message execution '''
        message = ReturnQueryDataRequest([0x0000]*2)
        self.assertEqual(message.encode(), '\x00\x00\x00\x00\x00\x00');
        message = ReturnQueryDataRequest(0x0000)
        self.assertEqual(message.encode(), '\x00\x00\x00\x00');

    def testReturnQueryDataResponse(self):
        ''' Testing diagnostic message execution '''
        message = ReturnQueryDataResponse([0x0000]*2)
        self.assertEqual(message.encode(), '\x00\x00\x00\x00\x00\x00');
        message = ReturnQueryDataResponse(0x0000)
        self.assertEqual(message.encode(), '\x00\x00\x00\x00');

    def testRestartCommunicationsOption(self):
        ''' Testing diagnostic message execution '''
        request = RestartCommunicationsOptionRequest(True);
        self.assertEqual(request.encode(), '\x00\x01\xff\x00')
        request = RestartCommunicationsOptionRequest(False);
        self.assertEqual(request.encode(), '\x00\x01\x00\x00')

        response = RestartCommunicationsOptionResponse(True);
        self.assertEqual(response.encode(), '\x00\x01\xff\x00')
        response = RestartCommunicationsOptionResponse(False);
        self.assertEqual(response.encode(), '\x00\x01\x00\x00')

    def testGetClearModbusPlusRequestExecute(self):
        ''' Testing diagnostic message execution '''
        request = GetClearModbusPlusRequest(ModbusPlusOperation.ClearStatistics);
        response = request.execute()
        self.assertEqual(response.message, None)

        request = GetClearModbusPlusRequest(ModbusPlusOperation.GetStatistics);
        response = request.execute()
        self.assertEqual(response.message, [0x00] * 55)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
