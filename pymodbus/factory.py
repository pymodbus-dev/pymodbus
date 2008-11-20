'''
The following implement modbus decoder factories

  * decodeModbusResponsePdu:
    decodes a modbus response message or returns an error response

  * decodeModbusRequestPdu:
    decodes a modbus request message or returns an illegal request message
'''

from pdu import IllegalFunctionRequest
from pdu import ExceptionResponse
from pdu import ModbusExceptions as mexcept

from mexceptions import ModbusException
from pymodbus.bit_read_message import *
from pymodbus.bit_write_message import *
from pymodbus.diag_message import *
from pymodbus.file_message import *
from pymodbus.other_message import *
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *

#---------------------------------------------------------------------------# 
# Logging
#---------------------------------------------------------------------------# 
from pymodbus.log import protocol_log as log

#---------------------------------------------------------------------------# 
# Request Message Factory
#---------------------------------------------------------------------------# 
# To add more implemented functions, simply add them to the list
#---------------------------------------------------------------------------# 
__request_function_table = [
	ReadHoldingRegistersRequest,
	ReadDiscreteInputsRequest,
	ReadInputRegistersRequest,
	ReadCoilsRequest,
	WriteMultipleCoilsRequest,
	WriteMultipleRegistersRequest,
	WriteSingleRegisterRequest,
	WriteSingleCoilRequest,
	ReadWriteMultipleRegistersRequest
]
__request_function_codes = [i.function_code for i in __request_function_table]

def decodeModbusRequestPDU(data):
	'''
	This factory is used to generate the correct request object
	from a valid request packet
	@param data The request packet to decode
	@return The decoded request or illegal function request object
	'''
	function_code = ord(data[0])
	log.debug("Factory Request[%d]" % function_code)
	if function_code in __request_function_codes:
		request = __request_function_table[
			__request_function_codes.index(function_code)]()
	else:
		request = IllegalFunctionRequest(function_code)
	request.decode(data[1:])
	return request           

#---------------------------------------------------------------------------# 
# Response Message Factory
#---------------------------------------------------------------------------# 
# To add more implemented functions, simply add them to the list
#---------------------------------------------------------------------------# 
__response_function_table = [
	ReadHoldingRegistersResponse,
	ReadDiscreteInputsResponse,
	ReadInputRegistersResponse,
	ReadCoilsResponse,
	WriteMultipleCoilsResponse,
	WriteMultipleRegistersResponse,
	WriteSingleRegisterResponse,
	WriteSingleCoilResponse,
	ReadWriteMultipleRegistersResponse
]
__response_function_codes = [i.function_code for i in __request_function_table]

def decodeModbusResponsePDU(data):
	'''
	This factory is used to generate the correct response object
	from a valid response packet
	@param data The response packet to decode
	@return The decoded request or an exception response object
	'''
	function_code = ord(data[0])
	log.debug("Factory Response[%d]" % function_code)
	if function_code in __response_function_codes:
		response = __response_function_table[
			__response_function_codes.index(function_code)]()
	elif function_code > 0x80:
		response = ExceptionResponse(function_code & 0x7f, mexcept.IllegalFunction)
	else:
		raise ModbusException("Unknown response %d" % function_code)
	response.decode(data[1:])
	return response

__all__ = ['decodeModbusResponsePdu', 'decodeModbusRequestPdu']
