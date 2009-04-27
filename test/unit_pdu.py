import unittest
from pymodbus.pdu import *
from pymodbus.mexceptions import *

class SimplePduTest(unittest.TestCase):
	'''
	This is the unittest for the pymod.pdu module
	'''

	def setUp(self):
		''' Initializes the test environment '''
		self.badRequests = (
		#	ModbusPDU(),
			ModbusRequest(),
			ModbusResponse(),
		)
		self.illegal = IllegalFunctionRequest(1)
		self.exception = ExceptionResponse(1,1)
	
	def tearDown(self):
		''' Cleans up the test environment '''
		del self.badRequests
		del self.illegal
		del self.exception

	def testNotImpelmented(self):
		''' Test a base classes for not implemented funtions '''
		for r in self.badRequests:
			self.assertRaises(NotImplementedException, r.encode)

		for r in self.badRequests:
			self.assertRaises(NotImplementedException, r.decode, None)

	def testErrorMethods(self):
		''' Test all error methods '''
		self.illegal.decode("12345")
		self.illegal.execute(None)
			
		result = self.exception.encode()
		self.exception.decode(result)
		self.assertTrue(result == '\x01',
			"ExceptionResponse encoded incorrectly")
		self.assertTrue(self.exception.exception_code == 1,
			"ExceptionResponse decoded incorrectly")

#---------------------------------------------------------------------------# 
# Main
#---------------------------------------------------------------------------# 
if __name__ == "__main__":
	unittest.main()
        
