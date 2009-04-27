'''
I'm not sure how wel this will work as we have the client try and run
as many request as it can as fast as it can without stopping, and then
finishing...hmmmm
'''
import unittest
from pymodbus.mexceptions import *
from pymodbus.diag_message import *

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
            (ClearCountersRequest,                          '\x00\x0a\x00\x00', '\x00\x0a\x00\x00'),
            (ReturnBusMessageCountRequest,                  '\x00\x0b\x00\x00', '\x00\x0b\x00\x00'),
            (ReturnBusCommunicationErrorCountRequest,       '\x00\x0c\x00\x00', '\x00\x0c\x00\x00'),
            (ReturnBusExceptionErrorCountRequest,           '\x00\x0d\x00\x00', '\x00\x0d\x00\x00'),
            (ReturnSlaveMessageCountRequest,                '\x00\x0e\x00\x00', '\x00\x0e\x00\x00'),
            (ReturnSlaveNoResponseCountRequest,             '\x00\x0f\x00\x00', '\x00\x0f\x00\x00'),
            (ReturnSlaveNAKCountRequest,                    '\x00\x10\x00\x00', '\x00\x10\x00\x00'),
            (ReturnSlaveBusyCountRequest,                   '\x00\x11\x00\x00', '\x00\x11\x00\x00'),
            (ReturnSlaveBusCharacterOverrunCountRequest,    '\x00\x12\x00\x00', '\x00\x12\x00\x00'),
            (ClearOverrunCountRequest,                      '\x00\x14\x00\x00', '\x00\x14\x00\x00'),
        ]

        self.responses = [
            #(DiagnosticStatusResponse,                     '\x00\x00\x00\x00'),
            #(DiagnosticStatusSimpleResponse,               '\x00\x00\x00\x00'),
            #(ReturnQueryDataResponse,                      '\x00\x00\x00\x00'),
            #(RestartCommunicationsOptionResponse,          '\x00\x01\x00\x00'),
            #(ReturnDiagnosticRegisterResponse,             '\x00\x02\x00\x00'),
            #(ChangeAsciiInputDelimiterResponse,            '\x00\x03\x00\x00'),
            #(ForceListenOnlyModeResponse,                  '\x00\x04'),
            #(ClearCountersResponse,                        '\x00\x0a\x00\x00'),
            #(ReturnBusMessageCountResponse,                '\x00\x0b\x00\x00'),
            #(ReturnBusCommunicationErrorCountResponse,     '\x00\x0c\x00\x00'),
            #(ReturnBusExceptionErrorCountResponse,         '\x00\x0d\x00\x00'),
            #(ReturnSlaveMessageCountResponse,              '\x00\x0e\x00\x00'),
            #(ReturnSlaveNoReponseCountResponse,            '\x00\x0f\x00\x00'),
            #(ReturnSlaveNAKCountResponse,                  '\x00\x10\x00\x00'),
            #(ReturnSlaveBusyCountResponse,                 '\x00\x11\x00\x00'),
            #(ReturnSlaveBusCharacterOverrunCountResponse,  '\x00\x12\x00\x00'),
            #(ClearOverrunCountResponse,                    '\x00\x14\x00\x00'),
        ]

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self.requests
        del self.responses

    def testDiagnosticRequests(self):
        ''' Testing diagnostic request messages encoding '''
        for msg,enc,exe in self.requests:
            self.assertTrue(msg,msg().encode() == enc)

    def testDiagnosticLoopbackRequest(self):
        ''' Testing diagnostic request messages encoding '''
        #r  = ReturnQueryDataRequest([0,1,2,3,4])
        #r.execute()

    def testDiagnosticResponse(self):
        ''' Testing diagnostic request messages '''
        for msg,enc in self.responses:
            self.assertTrue(msg,msg().encode() == enc)

    def testDiagnosticExecute(self):
        ''' Testing diagnostic message execution '''
        for msg,enc,exe in self.requests:
            self.assertTrue(msg().execute().encode() == exe)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
