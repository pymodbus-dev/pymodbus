'''
Modbus Server Datastore

For each server, you will create a ModbusServerContext and pass
in the default address space for each data access.  The class
will create and manage the data.

Further modification of said data accesses should be performed
with [get,set][access]Values(address, count)



Datastore Implementation

There are two ways that the server datastore can be implemented.
The first is a complete range from 'address' start to 'count'
number of indecies.  This can be thought of as a straight array:
	data = range(1, 1 + count)
	[1,2,3,...,count]

The other way that the datastore can be implemented (and how
many devices implement it) is a associate-array:
	data = {1:'1', 3:'3', ..., count:'count'}
	[1,3,...,count]

The difference between the two is that the latter will allow
arbitrary gaps in its datastore while the former will not.
This is seen quite commonly in devices with modbus implementations.
What follows is a clear example from the field:

Say a company makes two devices to monitor power usage on a rack.
One works with three-phase and the other with a single phase. The
company will dictate a modbus data mapping such that registers

	n:		phase 1 power
	n+1:	phase 2 power
	n+2:	phase 3 power

Using this, layout, the first device will implement n, n+1, and n+2,
however, the second device may set the latter two values to 0 or
will simply not implmented the registers thus causing a single read
or a range read to fail.

I have both methods implemented, and leave it up to the user to change
based on their preference
'''
from pymodbus.interfaces import Singleton
from pymodbus.mexceptions import *

#---------------------------------------------------------------------------# 
# Network Access Control
#---------------------------------------------------------------------------# 
class ModbusAccessControl(Singleton):
	'''
	This is a simple implementation of a Network Management System table.
	Its purpose is to control access to the server (if it is used).
	We assume that if an entry is in the table, it is allowed accesses to
	resources.  However, if the host does not appear in the table (all 
	unknown hosts) its connection will simply be closed.

	Since it is a singleton, only one version can possible exist and all
	instances pull from here.
	'''
	__nmstable = [
		"127.0.0.1",
	]

	def addAllowedHost(self, host):
		'''
		Add allowed host(s) from the NMS table
		@param host The host to add
		'''
		if not isinstance(host, list):
			host = [host]
		for entry in host: 
			self.__nmstable.append(host)

	def removeAllowedHost(self, host):
		'''
		Remove allowed host(s) from the NMS table
		@param host The host to remove
		'''
		if not isinstance(host, list):
			host = [host]
		for entry in host: 
			if host in self.__nmstable:
				self.__nmstable.remove(host)

	def checkHost(self, host):
		'''
		Check if a host is allowed to access resources
		@param host The host to check
		'''
		return host in self.__nmstable

#---------------------------------------------------------------------------# 
# Device Information Control
#---------------------------------------------------------------------------# 
class ModbusDeviceIdentification:
	'''
	This is used to supply the device identification
	for the readDeviceIdentification function

	For more information read section 6.21 of the modbus
	application protocol.
	'''
	_data = {
		0x00: '', # VendorName
		0x01: '', # ProductCode
		0x02: '', # MajorMinorRevision
		0x03: '', # VendorUrl
		0x04: '', # ProductName
		0x05: '', # ModelName
		0x06: '', # UserApplicationName
		0x07: '', # reserved
		0x08: '', # reserved
		# 0x80 -> 0xFF are private
	}
	
	def __init__(self, info=None):
		'''
		Initialize the datastore with the elements you need.
		(note acceptable range is [0x00-0x07,0x80-0xFF] inclusive)
		@param info A dictionary of {int:string} of values
		'''
		if info is not None and isinstance(info, dict):
			for i in info.keys():
				if (i < 0x07) or (i >= 0x80) or (i <= 0xff):
					self._data[i] = info[i]

	def getValue(self, address):
		'''
		Wrapper used to access the device information
		@param value The register to read
		'''
		if address in self._data.keys():
			return self._data[address]
		return None

	def setValue(self, address, value):
		'''
		Wrapper used to access the device information
		@param address The register to set
		@param value The new value for referenced register
		'''
		if address not in [0x07, 0x08]:
			self._data[address] = value

	def __str__(self):
		return "DeviceIdentity"

class ModbusControlBlock(Singleton):
	'''
	This is a global singleotn that controls all system information

	All activity should be logged here and all diagnostic requests
	should come from here.
	'''

	__counter = {
		'BusMessage'			: 0x0000,
		'BusCommunicationError'	: 0x0000,
		'BusExceptionError'		: 0x0000,
		'SlaveMessage'			: 0x0000,
		'SlaveNoResponse'		: 0x0000,
		'SlaveNAK'				: 0x0000,
		'SlaveBusy'				: 0x0000,
		'BusCharacterOverrun'	: 0x0000,
	}
	__mode = 'ASCII'
	__diagnostic = [False] * 16
	__instance = None
	__listen_only = False
	__delimiter = '\r'
	Identity = ModbusDeviceIdentification()

	def __str__(self):
		return "ModbusControl"

	#---------------------------------------------------------------------------# 
	# Conter Properties
	#---------------------------------------------------------------------------# 
	def resetAllCounters(self):
		''' This clears all of the system counters and diagnostic flags '''
		for i in self.__counter.keys():
			self.__counter[i] = 0x0000
		self.__diagnostic = [False] * 16

	def incrementCounter(self, counter):
		'''
		This increments a system counter
		@param counter The counter to increment
		'''
		if counter in self.__counter.keys():
			self.__counter[counter] += 1

	def getCounter(self, counter):
		'''
		This returns the requested counter
		@param counter The counter to return
		'''
		if counter in self.__counter.keys():
			return self.__counter[counter]
		return None

	def resetCounter(self, counter):
		''' This clears the selected counter '''
		if counter in self.__counter.keys():
			self.__counter[counter] = 0x0000

	#---------------------------------------------------------------------------# 
	# Listen Properties
	#---------------------------------------------------------------------------# 
	def toggleListenOnly(self):
		''' This toggles the listen only status '''
		self.__listen_only = not self.__listen_only

	def isListenOnly(self):
		''' This returns weither we should listen only '''
		return self.__listen_only

	#---------------------------------------------------------------------------# 
	# Mode Properties
	#---------------------------------------------------------------------------# 
	def setMode(self, mode):
		'''
		This toggles the current serial mode
		@param mode The data transfer method in (RTU, ASCII)
		'''
		if mode in ['ASCII', 'RTU']:
			self.__mode = mode

	def getMode(self):
		''' Returns the current transfer mode '''
		return self.__mode

	#---------------------------------------------------------------------------# 
	# Delimiter Properties
	#---------------------------------------------------------------------------# 
	def setDelimiter(self, char):
		'''
		This changes the serial delimiter character
		@param char The new serial delimiter character
		'''
		if isinstance(char, str):
			self.__delimiter = char
		elif isinstance(char, int):
			self.__delimiter = chr(char)

	def getDelimiter(self):
		''' Returns the current serial delimiter character '''
		return self.__delimiter

	#---------------------------------------------------------------------------# 
	# Diagnostic Properties
	#---------------------------------------------------------------------------# 
	def setDiagnostic(self, bit, value):
		'''
		This sets the value in the diagnostic register
		@param bit The bit to set
		@param value The value of set the bit as
		'''
		if (bit >= 0) or (bit < len(self.__diagnostic)):
			self.__diagnostic[bit] = (value != 0)

	def getDiagnosticRegisterBit(self, bit):
		'''
		This gets the value in the diagnostic register
		@param bit The bit to set
		'''
		if (bit >= 0) or (bit < len(self.__diagnostic)):
			return self.__diagnostic[bit]
		return None

	def getDiagnosticRegister(self):
		'''
		This gets the entire diagnostic register
		'''
		return self.__diagnostic

#---------------------------------------------------------------------------# 
# Datablock Storage
#---------------------------------------------------------------------------# 
class ModbusDataBlock:
	'''
	Base class for a modbus datastore

	Derived classes must create the following fields:
		@address The starting address point
		@defult_value The default value of the datastore
		@values The actual datastore values 

	Derived classes must implemented the following methods:
		checkAddress(self, address, count=1)
		getValues(self, address, count=1)
		setValues(self, address, values)
	'''

	def default(self, count, value):
		''' Used to initialize a store to one value '''
		self.default_value = value
		self.values = [default_value] * count

	def reset(self):
		''' Resets the datastore to the initialized default value '''
		for i in self.values:
			i = self.default_value

	def checkAddress(self, address, count=1):
		'''
		Checks to see if the request is in range
		@param address The starting address
		@param count The number of values to test for
		'''
		raise NotImplementedException("Datastore Address Check")

	def getValues(self, address, count=1):
		'''
		Returns the requested values from the datastore
		@param address The starting address
		@param count The number of values to retrieve
		'''
		raise NotImplementedException("Datastore Value Retrieve")

	def setValues(self, address, values):
		'''
		Returns the requested values from the datastore
		@param address The starting address
		@param values The values to store
		'''
		raise NotImplementedException("Datastore Value Retrieve")

	def __str__(self):
		return "DataStore(%d, %d)" % (self.address, self.default_value)

class ModbusSequentialDataBlock(ModbusDataBlock):
	''' Creates a sequential modbus datastore '''

	def __init__(self, address, values):
		'''
		Initializes the datastore
		@address The starting address of the datastore
		@values Either a list or a dictionary of values
		'''
		self.address = address
		if isinstance(values, list):
			self.values = values
		else: self.values = [values]
		self.default_value = self.values[0]

	def checkAddress(self, address, count=1):
		'''
		Checks to see if the request is in range
		@param address The starting address
		@param count The number of values to test for
		'''
		if self.address > address:
			return False
		if ((self.address + len(self.values)) < 
			(address + count)): return False
		return True

	def getValues(self, address, count=1):
		'''
		Returns the requested values of the datastore
		@param address The starting address
		@param count The number of values to retrieve
		'''
		b = address - self.address
		ret = self.values[b:b+count]
		return ret

	def setValues(self, address, values):
		'''
		Sets the requested values of the datastore
		@param address The starting address
		@param values The new values to be set
		'''
		b = address - self.address
		self.values[b:b+len(values)] = values

class ModbusSparseDataBlock(ModbusDataBlock):
	''' Creates a sparse modbus datastore '''

	def __init__(self, values):
		'''
		Initializes the datastore
		@values Either a list or a dictionary of values

		Using @values we create the default datastore value
		and the starting address
		'''
		if isinstance(values, dict):
			self.values = values
		elif isinstance(values, list):
			self.values = dict([(i,v) for i,v in enumerate(values)])
		else: raise ParameterException(
				"Values for datastore must be a list or dictionary")
		self.default_value = self.values.values()[0]
		self.address = self.values.iterkeys().next()

	def checkAddress(self, address, count=1):
		'''
		Checks to see if the request is in range
		@param address The starting address
		@param count The number of values to test for
		'''
		return set(range(address, address + count)
				).issubset(set(self.values.iterkeys()))

	def getValues(self, address, count=1):
		'''
		Returns the requested values of the datastore
		@param address The starting address
		@param count The number of values to retrieve
		'''
		return [self.values[i]
			for i in range(address, address + count)]

	def setValues(self, address, values):
		'''
		Sets the requested values of the datastore
		@param address The starting address
		@param values The new values to be set
		'''
		for i,v in enumerate(values):
			self.values[address + i] = v

#---------------------------------------------------------------------------# 
# Device Data Control
#---------------------------------------------------------------------------# 
class ModbusServerContext:
	'''
	This creates a modbus data model with each data access
	stored in its own personal block
	'''

	def __init__(self, **kwargs):
		'''
		Initializes the datastores
		@param kwargs
			Each element is a ModbusDataBlock
			'd' - Discrete Inputs initializer
			'c' - Coils initializer
			'h' - Holding Register initializer
			'i' - Input Registers iniatializer
		'''
		for k in ['d', 'c', 'h', 'i']:
			if not kwargs.has_key(k):
				kwargs[k] = ModbusSequentialDataBlock(0, 0)
			if not isinstance(kwargs[k], ModbusDataBlock):
				raise ParameterException(
					"Assigned datastore is not a ModbusDataBlock")
		self.di = kwargs['d']
		self.co = kwargs['c']
		self.ir = kwargs['i']
		self.hr = kwargs['h']

	def default(self, **kwargs):
		''' Restores each datastore to its default '''
		for i in [self.di, self.co, self.ir, self.hr]:
			i.default()
	
	def reset(self):
		''' Resets all the datastores '''
		for i in [self.di, self.co, self.ir, self.hr]:
			i.reset()

	#--------------------------------------------------------------------------#
	# Address Range Checkers
	#--------------------------------------------------------------------------#
	def checkCoilAddress(self, address, count=1):
		return self.co.checkAddress(address, count)
	
	def checkDiscreteInputAddress(self, address, count=1):
		return self.di.checkAddress(address, count)
	
	def checkInputRegisterAddress(self, address, count=1):
		return self.ir.checkAddress(address, count)
	
	def checkHoldingRegisterAddress(self, address, count=1):
		return self.hr.checkAddress(address, count)

	#--------------------------------------------------------------------------#
	# Current Value Getters
	#--------------------------------------------------------------------------#
	def getCoilValues(self, address, count=1):
		return self.co.getValues(address, count)
	
	def getDiscreteInputValues(self, address, count=1):
		return self.di.getValues(address, count)
	
	def getInputRegisterValues(self, address, count=1):
		return self.ir.getValues(address, count)
	
	def getHoldingRegisterValues(self, address, count=1):
		return self.hr.getValues(address, count)
	
	#--------------------------------------------------------------------------#
	# Current Value Setters
	#--------------------------------------------------------------------------#
	def setCoilValues(self, address, values):
		self.co.setValues(address, values)
	
	def setHoldingRegisterValues(self, address, values):
		self.hr.setValues(address, values)

	def __str__(self):
		return "Server Context\n", [self.co, self.di, self.ir, self.hr]

#__all__ = []
