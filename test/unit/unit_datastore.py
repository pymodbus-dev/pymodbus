import unittest
from pymodbus.datastore import *
from pymodbus.mexceptions import *

class SimpleDataStoreTest(unittest.TestCase):
	'''
	This is the unittest for the pymod.mexceptions module
	'''

	def setUp(self):
		info = {
			0x00: 'Bashwork',				# VendorName
			0x01: 'PTM',					# ProductCode
			0x02: '1.0',					# MajorMinorRevision
			0x03: 'http://internets.com',	# VendorUrl
			0x04: 'pymodbus',				# ProductName
			0x05: 'bashwork',				# ModelName
			0x06: 'unittest',				# UserApplicationName
			0x07: 'x',						# reserved
			0x08: 'x',						# reserved
			0x10: 'private'					# private data
		}
		self.ident = ModbusDeviceIdentification(info)
		self.control = ModbusControlBlock()
	
	def tearDown(self):
		''' Cleans up the test environment '''
		del self.ident
		del self.control

	def testModbusDeviceIdentificationGet(self):
		''' Test device identification reading '''
		self.assertTrue(self.ident.getValue(0x00) == 'Bashwork')
		self.assertTrue(self.ident.getValue(0x01) == 'PTM')
		self.assertTrue(self.ident.getValue(0x02) == '1.0')
		self.assertTrue(self.ident.getValue(0x03) == 'http://internets.com')
		self.assertTrue(self.ident.getValue(0x04) == 'pymodbus')
		self.assertTrue(self.ident.getValue(0x05) == 'bashwork')
		self.assertTrue(self.ident.getValue(0x06) == 'unittest')
		self.assertTrue(self.ident.getValue(0x07) == 'x')
		self.assertTrue(self.ident.getValue(0x08) == 'x')
		self.assertTrue(self.ident.getValue(0x10) == 'private')
		self.assertTrue(self.ident.getValue(0x54) == None)

	def testModbusDeviceIdentificationSet(self):
		''' Test a device identification writing '''
		self.ident.setValue(0x07, 'y')
		self.ident.setValue(0x08, 'y')
		self.ident.setValue(0x10, 'public')
		self.ident.setValue(0x54, 'testing')

		self.assertFalse(self.ident.getValue(0x07) == 'y')
		self.assertFalse(self.ident.getValue(0x08) == 'y')
		self.assertTrue(self.ident.getValue(0x10) == 'public')
		self.assertTrue(self.ident.getValue(0x54) == 'testing')

	def testModbusControlBlock(self):
		''' Test a server control block '''
		self.assertTrue(id(self.control) == id(ModbusControlBlock()))
		self.control.Identity = self.ident
		self.control.setMode('RTU')
		self.assertTrue(self.control.getMode() == 'RTU')
		self.control.setMode('FAKE')
		self.assertFalse(self.control.getMode() == 'FAKE')

	def testModbusDataBlock(self):
		''' Test a base data block store '''
		pass

	def testModbusSequentialDataBlock(self):
		''' Test a sequential data block store '''
		pass

	def testModbusSparseDataBlock(self):
		''' Test a sparse data block store '''
		pass

	def testServerContext(self):
		''' Test a modbus server context '''
		pass

#---------------------------------------------------------------------------# 
# Main
#---------------------------------------------------------------------------# 
if __name__ == "__main__":
	unittest.main()
        
	#c = ModbusServerContext(d=[0,100], c=[0,100], h=[0,100], i=[0,100])

	## Test Coils
	##-----------------------------------------------------------------------#
	#values = [True]*100
	#c.setCoilValues(0, values)
	#result = c.getCoilValues(0, 100)

	#if result == values: print "Coil Store Passed"

	## Test Discretes
	##-----------------------------------------------------------------------#
	#values = [False]*100
	#result = c.getDiscreteInputValues(0, 100)

	#if result == values: print "Discrete Store Passed"

	## Test Holding Registers
	##-----------------------------------------------------------------------#
	#values = [0xab]*100
	#c.setHoldingRegisterValues(0, values)
	#result = c.getHoldingRegisterValues(0, 100)

	#if result == values: print "Holding Register Store Passed"

	## Test Input Registers
	##-----------------------------------------------------------------------#
	#values = [0x00]*100
	#result = c.getInputRegisterValues(0, 100)

	#if result == values: print "Input Register Store Passed"
