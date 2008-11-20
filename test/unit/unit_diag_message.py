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
			#(DiagnosticStatusRequest,						0x0000),
			#(DiagnosticStatusSimpleRequest,				0x0000),
			#(ReturnQueryDataRequest,						0x0000),
			(RestartCommunicationsOptionRequest,			0x0000),
			(ReturnDiagnosticRegisterRequest,				0x0000),
			(ChangeAsciiInputDelimiterRequest,				0x0000),
			(ForceListenOnlyModeRequest,					0x0000),
			(ClearCountersRequest,							0x0000),
			(ReturnBusMessageCountRequest,					0x0000),
			(ReturnBusCommunicationErrorCountRequest,		0x0000),
			(ReturnBusExceptionErrorCountRequest,			0x0000),
			(ReturnSlaveMessageCountRequest,				0x0000),
			(ReturnSlaveNoResponseCountRequest,				0x0000),
			(ReturnSlaveNAKCountRequest,					0x0000),
			(ReturnSlaveBusyCountRequest,					0x0000),
			(ReturnSlaveBusCharacterOverrunCountRequest,	0x0000),
			(ClearOverrunCountRequest,						0x0000),
		]

		self.responses = [
			#DiagnosticStatusResponse,
			#DiagnosticStatusSimpleResponse,
			#ReturnQueryDataResponse,
			#RestartCommunicationsOptionResponse,
			#ReturnDiagnosticRegisterResponse,
			#ChangeAsciiInputDelimiterResponse,
			#ForceListenOnlyModeResponse,
			#ClearCountersResponse,
			#ReturnBusMessageCountResponse,
			#ReturnBusCommunicationErrorCountResponse,
			#ReturnBusExceptionErrorCountResponse,
			#ReturnSlaveMessageCountResponse,
			#ReturnSlaveNoReponseCountResponse,
			#ReturnSlaveNAKCountResponse,
			#ReturnSlaveBusyCountResponse,
			#ReturnSlaveBusCharacterOverrunCountResponse,
			#ClearOverrunCountResponse,
		]

	def tearDown(self):
		''' Cleans up the test environment '''
		del self.requests
		del self.responses

	def testDiagnosticRequests(self):
		''' Testing diagnostic request messages '''
		for msg,rslt in enumerate(self.requests):
			print msg,msg().encode().encode('hex')

	def testDiagnosticResponse(self):
		''' Testing diagnostic request messages '''
		for msg,rslt in enumerate(self.requests):
			print msg,msg().encode().encode('hex')

	def testDiagnosticExecute(self):
		''' Testing diagnostic message execution '''
		for msg,rslt in enumerate(self.requests):
			print msg().execute().encode().encode('hex')

#---------------------------------------------------------------------------# 
# Main
#---------------------------------------------------------------------------# 
if __name__ == "__main__":
	unittest.main()
