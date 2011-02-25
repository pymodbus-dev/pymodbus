"""
Modbus Request/Response Decoder Factories
-------------------------------------------

"""

from pymodbus.pdu import IllegalFunctionRequest
from pymodbus.pdu import ExceptionResponse
from pymodbus.pdu import ModbusExceptions as ecode
from pymodbus.interfaces import IModbusDecoder
from pymodbus.exceptions import ModbusException
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
import logging
_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Server Decoder
#---------------------------------------------------------------------------#

class ServerDecoder(IModbusDecoder):
    ''' Request Message Factory (Server)

    To add more implemented functions, simply add them to the list
    '''
    __function_table = [
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
    __lookup = dict([(f.function_code, f) for f in __function_table])

    def decode(self, message):
        ''' Wrapper to decode a request packet

        :param message: The raw modbus request packet
        :return: The decoded modbus message or None if error
        '''
        try:
            return self._helper(message)
        except ModbusException, er:
            _logger.warn("Unable to decode request %s" % er)
        return None

    def lookupPduClass(self, function_code):
        ''' Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        '''
        return self.__lookup.get(function_code, None)

    def _helper(self, data):
        '''
        This factory is used to generate the correct request object
        from a valid request packet. This decodes from a list of the
        currently implemented request types.

        :param data: The request packet to decode
        :returns: The decoded request or illegal function request object
        '''
        function_code = ord(data[0])
        _logger.debug("Factory Request[%d]" % function_code)
        request = self.__lookup.get(function_code, lambda: None)()
        if not request:
            request = IllegalFunctionRequest(function_code)
        request.decode(data[1:])
        return request

#---------------------------------------------------------------------------# 
# Client Decoder
#---------------------------------------------------------------------------# 

class ClientDecoder(IModbusDecoder):
    ''' Response Message Factory (Client)

    To add more implemented functions, simply add them to the list
    '''
    __function_table = [
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
    __lookup = dict([(f.function_code, f) for f in __function_table])

    def lookupPduClass(self, function_code):
        ''' Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        '''
        return self.__lookup.get(function_code, None)

    def decode(self, message):
        ''' Wrapper to decode a response packet

        :param message: The raw packet to decode
        :return: The decoded modbus message or None if error
        '''
        try:
            return self._helper(message)
        except ModbusException, er:
            _logger.error("Unable to decode response %s" % er)
        return None

    def _helper(self, data):
        '''
        This factory is used to generate the correct response object
        from a valid response packet. This decodes from a list of the
        currently implemented request types.

        :param data: The response packet to decode
        :returns: The decoded request or an exception response object
        '''
        function_code = ord(data[0])
        _logger.debug("Factory Response[%d]" % function_code)
        response = self.__lookup.get(function_code, lambda: None)()
        if function_code > 0x80:
            code = function_code & 0x7f # strip error portion
            response = ExceptionResponse(code, ecode.IllegalFunction)
        if not response:
            raise ModbusException("Unknown response %d" % function_code)
        response.decode(data[1:])
        return response

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = ['ServerDecoder', 'ClientDecoder']
