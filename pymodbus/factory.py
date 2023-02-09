"""Modbus Request/Response Decoder Factories.

The following factories make it easy to decode request/response messages.
To add a new request/response pair to be decodeable by the library, simply
add them to the respective function lookup table (order doesn't matter, but
it does help keep things organized).

Regardless of how many functions are added to the lookup, O(1) behavior is
kept as a result of a pre-computed lookup dictionary.
"""
# pylint: disable=missing-type-doc
from pymodbus.bit_read_message import (
    ReadCoilsRequest,
    ReadCoilsResponse,
    ReadDiscreteInputsRequest,
    ReadDiscreteInputsResponse,
)
from pymodbus.bit_write_message import (
    WriteMultipleCoilsRequest,
    WriteMultipleCoilsResponse,
    WriteSingleCoilRequest,
    WriteSingleCoilResponse,
)
from pymodbus.diag_message import (
    ChangeAsciiInputDelimiterRequest,
    ChangeAsciiInputDelimiterResponse,
    ClearCountersRequest,
    ClearCountersResponse,
    ClearOverrunCountRequest,
    ClearOverrunCountResponse,
    DiagnosticStatusRequest,
    DiagnosticStatusResponse,
    ForceListenOnlyModeRequest,
    ForceListenOnlyModeResponse,
    GetClearModbusPlusRequest,
    GetClearModbusPlusResponse,
    RestartCommunicationsOptionRequest,
    RestartCommunicationsOptionResponse,
    ReturnBusCommunicationErrorCountRequest,
    ReturnBusCommunicationErrorCountResponse,
    ReturnBusExceptionErrorCountRequest,
    ReturnBusExceptionErrorCountResponse,
    ReturnBusMessageCountRequest,
    ReturnBusMessageCountResponse,
    ReturnDiagnosticRegisterRequest,
    ReturnDiagnosticRegisterResponse,
    ReturnIopOverrunCountRequest,
    ReturnIopOverrunCountResponse,
    ReturnQueryDataRequest,
    ReturnQueryDataResponse,
    ReturnSlaveBusCharacterOverrunCountRequest,
    ReturnSlaveBusCharacterOverrunCountResponse,
    ReturnSlaveBusyCountRequest,
    ReturnSlaveBusyCountResponse,
    ReturnSlaveMessageCountRequest,
    ReturnSlaveMessageCountResponse,
    ReturnSlaveNAKCountRequest,
    ReturnSlaveNAKCountResponse,
    ReturnSlaveNoReponseCountResponse,
    ReturnSlaveNoResponseCountRequest,
)
from pymodbus.exceptions import MessageRegisterException, ModbusException
from pymodbus.file_message import (
    ReadFifoQueueRequest,
    ReadFifoQueueResponse,
    ReadFileRecordRequest,
    ReadFileRecordResponse,
    WriteFileRecordRequest,
    WriteFileRecordResponse,
)
from pymodbus.interfaces import IModbusDecoder
from pymodbus.logging import Log
from pymodbus.mei_message import (
    ReadDeviceInformationRequest,
    ReadDeviceInformationResponse,
)
from pymodbus.other_message import (
    GetCommEventCounterRequest,
    GetCommEventCounterResponse,
    GetCommEventLogRequest,
    GetCommEventLogResponse,
    ReadExceptionStatusRequest,
    ReadExceptionStatusResponse,
    ReportSlaveIdRequest,
    ReportSlaveIdResponse,
)
from pymodbus.pdu import ExceptionResponse, IllegalFunctionRequest
from pymodbus.pdu import ModbusExceptions as ecode
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
    ReadInputRegistersRequest,
    ReadInputRegistersResponse,
    ReadWriteMultipleRegistersRequest,
    ReadWriteMultipleRegistersResponse,
)
from pymodbus.register_write_message import (
    MaskWriteRegisterRequest,
    MaskWriteRegisterResponse,
    WriteMultipleRegistersRequest,
    WriteMultipleRegistersResponse,
    WriteSingleRegisterRequest,
    WriteSingleRegisterResponse,
)


# --------------------------------------------------------------------------- #
# Server Decoder
# --------------------------------------------------------------------------- #
class ServerDecoder(IModbusDecoder):
    """Request Message Factory (Server).

    To add more implemented functions, simply add them to the list
    """

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
        """Initialize the client lookup tables."""
        functions = {f.function_code for f in self.__function_table}
        self.__lookup = {f.function_code: f for f in self.__function_table}
        self.__sub_lookup = {f: {} for f in functions}
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def decode(self, message):
        """Decode a request packet

        :param message: The raw modbus request packet
        :return: The decoded modbus message or None if error
        """
        try:
            return self._helper(message)
        except ModbusException as exc:
            Log.warning("Unable to decode request {}", exc)
        return None

    def lookupPduClass(self, function_code):
        """Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        """
        return self.__lookup.get(function_code, ExceptionResponse)

    def _helper(self, data):
        """Generate the correct request object from a valid request packet.

        This decodes from a list of the currently implemented request types.

        :param data: The request packet to decode
        :returns: The decoded request or illegal function request object
        """
        function_code = int(data[0])
        if not (request := self.__lookup.get(function_code, lambda: None)()):
            Log.debug("Factory Request[{}]", function_code)
            request = IllegalFunctionRequest(function_code)
        else:
            fc_string = "%s: %s" % (  # pylint: disable=consider-using-f-string
                str(self.__lookup[function_code])  # pylint: disable=use-maxsplit-arg
                .split(".")[-1]
                .rstrip('">"'),
                function_code,
            )
            Log.debug("Factory Request[{}]", fc_string)
        request.decode(data[1:])

        if hasattr(request, "sub_function_code"):
            lookup = self.__sub_lookup.get(request.function_code, {})
            if subtype := lookup.get(request.sub_function_code, None):
                request.__class__ = subtype

        return request

    def register(self, function=None):
        """Register a function and sub function class with the decoder.

        :param function: Custom function class to register
        :raises MessageRegisterException:
        """
        if function and not issubclass(function, ModbusRequest):
            raise MessageRegisterException(
                f'"{function.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from "
                "`pymodbus.pdu.ModbusRequest` "
            )
        self.__lookup[function.function_code] = function
        if hasattr(function, "sub_function_code"):
            if function.function_code not in self.__sub_lookup:
                self.__sub_lookup[function.function_code] = {}
            self.__sub_lookup[function.function_code][
                function.sub_function_code
            ] = function


# --------------------------------------------------------------------------- #
# Client Decoder
# --------------------------------------------------------------------------- #
class ClientDecoder(IModbusDecoder):
    """Response Message Factory (Client).

    To add more implemented functions, simply add them to the list
    """

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
        """Initialize the client lookup tables."""
        functions = {f.function_code for f in self.__function_table}
        self.__lookup = {f.function_code: f for f in self.__function_table}
        self.__sub_lookup = {f: {} for f in functions}
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def lookupPduClass(self, function_code):
        """Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        """
        return self.__lookup.get(function_code, ExceptionResponse)

    def decode(self, message):
        """Decode a response packet.

        :param message: The raw packet to decode
        :return: The decoded modbus message or None if error
        """
        try:
            return self._helper(message)
        except ModbusException as exc:
            Log.error("Unable to decode response {}", exc)
        except Exception as exc:  # pylint: disable=broad-except
            Log.error("General exception: {}", exc)
        return None

    def _helper(self, data):
        """Generate the correct response object from a valid response packet.

        This decodes from a list of the currently implemented request types.

        :param data: The response packet to decode
        :returns: The decoded request or an exception response object
        :raises ModbusException:
        """
        fc_string = function_code = int(data[0])
        if function_code in self.__lookup:
            fc_string = "%s: %s" % (  # pylint: disable=consider-using-f-string
                str(self.__lookup[function_code])  # pylint: disable=use-maxsplit-arg
                .split(".")[-1]
                .rstrip('">"'),
                function_code,
            )
        Log.debug("Factory Response[{}]", fc_string)
        response = self.__lookup.get(function_code, lambda: None)()
        if function_code > 0x80:
            code = function_code & 0x7F  # strip error portion
            response = ExceptionResponse(code, ecode.IllegalFunction)
        if not response:
            raise ModbusException(f"Unknown response {function_code}")
        response.decode(data[1:])

        if hasattr(response, "sub_function_code"):
            lookup = self.__sub_lookup.get(response.function_code, {})
            if subtype := lookup.get(response.sub_function_code, None):
                response.__class__ = subtype

        return response

    def register(self, function):
        """Register a function and sub function class with the decoder."""
        if function and not issubclass(function, ModbusResponse):
            raise MessageRegisterException(
                f'"{function.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from "
                "`pymodbus.pdu.ModbusResponse` "
            )
        self.__lookup[function.function_code] = function
        if hasattr(function, "sub_function_code"):
            if function.function_code not in self.__sub_lookup:
                self.__sub_lookup[function.function_code] = {}
            self.__sub_lookup[function.function_code][
                function.sub_function_code
            ] = function


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = ["ServerDecoder", "ClientDecoder"]
