'''
Diagnostic record read/write

Currently not implemented
'''

from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.pdu import ModbusExceptions as merror
import struct

#---------------------------------------------------------------------------# 
# TODO Make these only work on serial
#---------------------------------------------------------------------------# 

class ReadExceptionStatusRequest(ModbusRequest):
	'''
	This function code is used to read the contents of eight Exception Status
   	outputs in a remote device.  The function provides a simple method for
   	accessing this information, because the Exception Output references are
   	known (no output reference is needed in the function).
	'''
	function_code = 0x07

	def __init__(self):
		ModbusRequest.__init__(self)

	def execute(self, status):
		#if cannot_read_status:
		#	return self.doException(merror.SlaveFailure)
		return ReadExceptionStatusResponse(status)

class ReadExceptionStatusResponse(ModbusResponse):
	'''
	The normal response contains the status of the eight Exception Status
   	outputs. The outputs are packed into one data byte, with one bit
   	per output. The status of the lowest output reference is contained
   	in the least significant bit of the byte.  The contents of the eight
   	Exception Status outputs are device specific.
	'''
	function_code = 0x07

	def __init__(self, status):
		ModbusRequest.__init__(self)
		self.status = status

	def encode(self):
		ret = struct.pack('>B', self.status)
		return ret

	def decode(self, data):
		self.status = struct.unpack('>B', data)

#---------------------------------------------------------------------------# 
# Diagnostic Function Codes
# diagnostic 08, 00-18,20
#---------------------------------------------------------------------------# 
# TODO Make these only work on serial
#---------------------------------------------------------------------------# 
class DiagnosticStatusRequest(ModbusRequest):
	'''
	This is a base class for all of the diagnostic request functions
	'''
	function_code = 0x08

	def __init__(self):
		ModbusRequest.__init__(self)

	def encode(self):
		ret = struct.pack('>H', self.sub_function_code)
		return ret

	def decode(self, data):
		self.sub_function_code = struct.unpack('>H', data)

class DiagnosticStatusResponse(ModbusResponse):
	'''
	This is a base class for all of the diagnostic response functions

	It works by performing all of the encoding and decoding of variable
	data and lets the higher classes define what extra data to append
	and how to execute a request
	'''
	function_code = 0x08

	def __init__(self):
		ModbusRequest.__init__(self)

	def encode(self):
		ret = struct.pack('>H', self.sub_function_code)
		if self.message:
			for r in self.message:
				ret += struct.pack('>H', r)
		return ret

	def decode(self, data):
		self.sub_function_code = struct.unpack('>H', data)


#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 00
#---------------------------------------------------------------------------# 
class ReturnQueryDataRequest(DiagnosticStatusRequest):
	'''
	To document
	'''
	sub_function_code = 0x0000

	def __init__(self, message):
		DiagnosticStatusRequest.__init__(self)
		if isinstance(message, list):
			self.message = message
		else: self.message = [message]

	def execute(self):
		return ReturnQueryDataResponse(self.message)

class ReturnQueryDataResponse(DiagnosticStatusResponse):
	'''
	To document
	'''
	sub_function_code = 0x0000

	def __init__(self, message):
		DiagnosticStatusResponse.__init__(self)
		if isinstance(message, list):
			self.message = message
		else: self.message = [message]

#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 01
#---------------------------------------------------------------------------# 
# TODO check for listen only mode
#---------------------------------------------------------------------------# 
class RestartCommunicationsOptionRequest(DiagnosticStatusRequest):
	'''
	To document
	'''
	sub_function_code = 0x0001

	def __init__(self, toggle=False):
		DiagnosticStatusRequest.__init__(self)
		if toggle:
			self.message = [0xff00]
		else: self.message = [0x0000]
	
	def execute(self):
		'''
		Clear event log and restart 
		'''
		return RestartCommunicationsOptionResponse(self.toggle)

class RestartCommunicationsOptionResponse(DiagnosticStatusResponse):
	'''
	To document
	'''
	sub_function_code = 0x0001

	def __init__(self, toggle=False):
		DiagnosticStatusResponse.__init__(self)
		if toggle:
			self.message = [0xff00]
		else: self.message = [0x0000]

#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 02
#---------------------------------------------------------------------------# 
# TODO check for listen only mode
#---------------------------------------------------------------------------# 
class ReturnDiagnosticRegisterRequest(DiagnosticStatusRequest):
	'''
	To document
	'''
	sub_function_code = 0x0002

	def __init__(self):
		DiagnosticStatusRequest.__init__(self)
		self.message = [0x0000]

	def execute(self, register):
		'''
		Clear event log and restart 
		'''
		return ReturnDiagnosticRegisterResponse(self.register)

class ReturnDiagnosticRegisterResponse(DiagnosticStatusResponse):
	'''
	To document
	'''
	sub_function_code = 0x0002

	def __init__(self, register):
		DiagnosticStatusResponse.__init__(self)
		self.message = register

#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 03
#---------------------------------------------------------------------------# 
class ChangeAsciiInputDelimiterRequest(DiagnosticStatusRequest):
	'''
	To document
	'''
	sub_function_code = 0x0003

	def __init__(self, char):
		DiagnosticStatusRequest.__init__(self)
		self.message = [char]

	def execute(self):
		'''
		For future serial messages, use char for delimiter
		'''
		return ChangeAsciiInputDelimiterResponse(self.message)

class ChangeAsciiInputDelimiterResponse(DiagnosticStatusResponse):
	'''
	To document
	'''
	sub_function_code = 0x0003

	def __init__(self, char):
		DiagnosticStatusResponse.__init__(self)
		self.message = [char]

#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 04
#---------------------------------------------------------------------------# 
class ForceListenOnlyModeRequest(DiagnosticStatusRequest):
	'''
	'''
	sub_function_code = 0x0004

	def __init__(self, char):
		DiagnosticStatusRequest.__init__(self)
		self.message = [0x0000]

	def execute(self):
		return ForceListenOnlyModeResponse()

class ForceListenOnlyModeResponse(DiagnosticStatusResponse):
	'''
	To document
	'''
	sub_function_code = 0x0004

	def __init__(self):
		DiagnosticStatusResponse.__init__(self)
		self.message = None

#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 10
#---------------------------------------------------------------------------# 
class ClearCountersRequest(DiagnosticStatusRequest):
	'''
	The goal is to clear ll counters and the diagnostic register.
	Also, counters are cleared upon power-up
	'''
	sub_function_code = 0x000A

	def __init__(self):
		DiagnosticStatusRequest.__init__(self)
		self.message = [0x0000]

	def execute(self):
		return ClearCountersResponse(self.message)

class ClearCountersResponse(DiagnosticStatusResponse):
	'''
	The goal is to clear ll counters and the diagnostic register.
	Also, counters are cleared upon power-up
	'''
	sub_function_code = 0x000A

	def __init__(self, message):
		DiagnosticStatusResponse.__init__(self)
		self.message = message

#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 11
#---------------------------------------------------------------------------# 
class ReturnBusMessageCountRequest(DiagnosticStatusRequest):
	'''
	The response data field returns the quantity of messages that the
	remote device has detected on the communications systems since its last
	restart, clear counters operation, or power-up
	'''
	sub_function_code = 0x000B

	def __init__(self):
		DiagnosticStatusRequest.__init__(self)
		self.message = [0x0000]

	def execute(self, count):
		return ReturnBusMessageCountResponse(count)

class ReturnBusMessageCountResponse(DiagnosticStatusResponse):
	'''
	The response data field returns the quantity of messages that the
	remote device has detected on the communications systems since its last
	restart, clear counters operation, or power-up
	'''
	sub_function_code = 0x000B

	def __init__(self, count):
		DiagnosticStatusResponse.__init__(self)
		self.message = [count]

#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 12
#---------------------------------------------------------------------------# 
class ReturnBusExceptionErrorCountRequest(DiagnosticStatusRequest):
	'''
	The response data field returns the quantity of modbus exception
	responses returned by the remote device since its last restart,
	clear counters operation, or power-up
	'''
	sub_function_code = 0x000C

	def __init__(self):
		DiagnosticStatusRequest.__init__(self)
		self.message = [0x0000]

	def execute(self, count):
		return ReturnBusExceptionErrorCountResponse(count)

class ReturnBusExceptionErrorCountResponse(DiagnosticStatusResponse):
	'''
	The response data field returns the quantity of modbus exception
	responses returned by the remote device since its last restart,
	clear counters operation, or power-up
	'''
	sub_function_code = 0x000C

	def __init__(self, count):
		DiagnosticStatusResponse.__init__(self)
		self.message = [count]

#---------------------------------------------------------------------------# 
# Diagnostic Sub Code 10
#---------------------------------------------------------------------------# 
#class Request(DiagnosticStatusRequest):
#	'''
#	To document
#	'''
#	sub_function_code = 0x000A
#
#	def __init__(self, char):
#		DiagnosticStatusRequest.__init__(self)
#		self.message = [char]
#
#	def execute(self):
#		return Response(self.message)
#
#class Response(DiagnosticStatusResponse):
#	'''
#	To document
#	'''
#	sub_function_code = 0x0003
#
#	def __init__(self, char):
#		DiagnosticStatusResponse.__init__(self)
#		self.message = [char]

#---------------------------------------------------------------------------# 
# To Be Completed
#---------------------------------------------------------------------------# 
# TODO Make these only work on serial
#---------------------------------------------------------------------------# 
# get com event counter 11
# get com event log 12
# report slave id 17
# report device identification 43, 14

#__all__ = []
