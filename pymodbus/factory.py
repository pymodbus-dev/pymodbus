"""
Modbus Request/Response Decoder Factories
-------------------------------------------

The following factories make it easy to decode request/response messages.
To add a new request/response pair to be decodeable by the library, simply
add them to the respective function lookup table (order doesn't matter, but
it does help keep things organized).

Regardless of how many functions are added to the lookup, O(1) behavior is
kept as a result of a pre-computed lookup dictionary.
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
from pymodbus.mei_message import *
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *
from pymodbus.compat import byte2int

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
            ReadWriteMultipleRegistersRequest,

            DiagnosticStatusRequest,

            ReadExceptionStatusRequest,
            GetCommEventCounterRequest,
            GetCommEventLogRequest,
            ReportSlaveIdRequest,

            ReadFileRecordRequest,
            WriteFileRecordRequest,
            MaskWriteRegisterRequest,
            ReadFifoQueueRequest,

            ReadDeviceInformationRequest,
    ]
    __sub_function_table = [
            ReturnQueryDataRequest,
            RestartCommunicationsOptionRequest,
            ReturnDiagnosticRegisterRequest,
            ChangeAsciiInputDelimiterRequest,
            ForceListenOnlyModeRequest,
            ClearCountersRequest,
            ReturnBusMessageCountRequest,
            ReturnBusCommunicationErrorCountRequest,
            ReturnBusExceptionErrorCountRequest,
            ReturnSlaveMessageCountRequest,
            ReturnSlaveNoResponseCountRequest,
            ReturnSlaveNAKCountRequest,
            ReturnSlaveBusyCountRequest,
            ReturnSlaveBusCharacterOverrunCountRequest,
            ReturnIopOverrunCountRequest,
            ClearOverrunCountRequest,
            GetClearModbusPlusRequest,

            ReadDeviceInformationRequest,
    ]

    def __init__(self):
        ''' Initializes the client lookup tables
        '''
        functions = set(f.function_code for f in self.__function_table)
        self.__lookup = dict([(f.function_code, f) for f in self.__function_table])
        self.__sub_lookup = dict((f, {}) for f in functions)
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def decode(self, message):
        ''' Wrapper to decode a request packet

        :param message: The raw modbus request packet
        :return: The decoded modbus message or None if error
        '''
        try:
            return self._helper(message)
        except ModbusException as er:
            _logger.warning("Unable to decode request %s" % er)
        return None

    def lookupPduClass(self, function_code):
        ''' Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        '''
        return self.__lookup.get(function_code, ExceptionResponse)

    def _helper(self, data):
        '''
        This factory is used to generate the correct request object
        from a valid request packet. This decodes from a list of the
        currently implemented request types.

        :param data: The request packet to decode
        :returns: The decoded request or illegal function request object
        '''
        function_code = byte2int(data[0])
        _logger.debug("Factory Request[%d]" % function_code)
        request = self.__lookup.get(function_code, lambda: None)()
        if not request:
            request = IllegalFunctionRequest(function_code)
        request.decode(data[1:])

        if hasattr(request, 'sub_function_code'):
            lookup = self.__sub_lookup.get(request.function_code, {})
            subtype = lookup.get(request.sub_function_code, None)
            if subtype: request.__class__ = subtype

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
            ReadWriteMultipleRegistersResponse,

            DiagnosticStatusResponse,

            ReadExceptionStatusResponse,
            GetCommEventCounterResponse,
            GetCommEventLogResponse,
            ReportSlaveIdResponse,

            ReadFileRecordResponse,
            WriteFileRecordResponse,
            MaskWriteRegisterResponse,
            ReadFifoQueueResponse,

            ReadDeviceInformationResponse,
    ]
    __sub_function_table = [
            ReturnQueryDataResponse,
            RestartCommunicationsOptionResponse,
            ReturnDiagnosticRegisterResponse,
            ChangeAsciiInputDelimiterResponse,
            ForceListenOnlyModeResponse,
            ClearCountersResponse,
            ReturnBusMessageCountResponse,
            ReturnBusCommunicationErrorCountResponse,
            ReturnBusExceptionErrorCountResponse,
            ReturnSlaveMessageCountResponse,
            ReturnSlaveNoReponseCountResponse,
            ReturnSlaveNAKCountResponse,
            ReturnSlaveBusyCountResponse,
            ReturnSlaveBusCharacterOverrunCountResponse,
            ReturnIopOverrunCountResponse,
            ClearOverrunCountResponse,
            GetClearModbusPlusResponse,

            ReadDeviceInformationResponse,
    ]

    def __init__(self):
        ''' Initializes the client lookup tables
        '''
        functions = set(f.function_code for f in self.__function_table)
        self.__lookup = dict([(f.function_code, f) for f in self.__function_table])
        self.__sub_lookup = dict((f, {}) for f in functions)
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def lookupPduClass(self, function_code):
        ''' Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        '''
        return self.__lookup.get(function_code, ExceptionResponse)

    def decode(self, message):
        ''' Wrapper to decode a response packet

        :param message: The raw packet to decode
        :return: The decoded modbus message or None if error
        '''
        try:
            return self._helper(message)
        except ModbusException as er:
            _logger.error("Unable to decode response %s" % er)

        except Exception as ex:
            _logger.error(ex)
        return None

    def _helper(self, data):
        '''
        This factory is used to generate the correct response object
        from a valid response packet. This decodes from a list of the
        currently implemented request types.

        :param data: The response packet to decode
        :returns: The decoded request or an exception response object
        '''
        fc_string = function_code = byte2int(data[0])
        if function_code in self.__lookup:
            fc_string = "%s: %s" % (
                str(self.__lookup[function_code]).split('.')[-1].rstrip("'>"),
                function_code
            )
        _logger.debug("Factory Response[%s]" % fc_string)
        response = self.__lookup.get(function_code, lambda: None)()
        if function_code > 0x80:
            code = function_code & 0x7f  # strip error portion
            response = ExceptionResponse(code, ecode.IllegalFunction)
        if not response:
            raise ModbusException("Unknown response %d" % function_code)
        response.decode(data[1:])

        if hasattr(response, 'sub_function_code'):
            lookup = self.__sub_lookup.get(response.function_code, {})
            subtype = lookup.get(response.sub_function_code, None)
            if subtype: response.__class__ = subtype

        return response

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = ['ServerDecoder', 'ClientDecoder']
