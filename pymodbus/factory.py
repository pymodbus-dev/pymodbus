"""Modbus Request/Response Decoder Factories.

The following factories make it easy to decode request/response messages.
To add a new request/response pair to be decodeable by the library, simply
add them to the respective function lookup table (order doesn't matter, but
it does help keep things organized).

Regardless of how many functions are added to the lookup, O(1) behavior is
kept as a result of a pre-computed lookup dictionary.
"""

# pylint: disable=missing-type-doc
from typing import Callable, Dict

from pymodbus import bit_read_message as bit_r_msg
from pymodbus import bit_write_message as bit_w_msg
from pymodbus import diag_message as diag_msg
from pymodbus import file_message as file_msg
from pymodbus import mei_message as mei_msg
from pymodbus import other_message as o_msg
from pymodbus import pdu
from pymodbus import register_read_message as reg_r_msg
from pymodbus import register_write_message as reg_w_msg
from pymodbus.exceptions import MessageRegisterException, ModbusException
from pymodbus.logging import Log


# --------------------------------------------------------------------------- #
# Server Decoder
# --------------------------------------------------------------------------- #
class ServerDecoder:
    """Request Message Factory (Server).

    To add more implemented functions, simply add them to the list
    """

    __function_table = [
        reg_r_msg.ReadHoldingRegistersRequest,
        bit_r_msg.ReadDiscreteInputsRequest,
        reg_r_msg.ReadInputRegistersRequest,
        bit_r_msg.ReadCoilsRequest,
        bit_w_msg.WriteMultipleCoilsRequest,
        reg_w_msg.WriteMultipleRegistersRequest,
        reg_w_msg.WriteSingleRegisterRequest,
        bit_w_msg.WriteSingleCoilRequest,
        reg_r_msg.ReadWriteMultipleRegistersRequest,
        diag_msg.DiagnosticStatusRequest,
        o_msg.ReadExceptionStatusRequest,
        o_msg.GetCommEventCounterRequest,
        o_msg.GetCommEventLogRequest,
        o_msg.ReportSlaveIdRequest,
        file_msg.ReadFileRecordRequest,
        file_msg.WriteFileRecordRequest,
        reg_w_msg.MaskWriteRegisterRequest,
        file_msg.ReadFifoQueueRequest,
        mei_msg.ReadDeviceInformationRequest,
    ]
    __sub_function_table = [
        diag_msg.ReturnQueryDataRequest,
        diag_msg.RestartCommunicationsOptionRequest,
        diag_msg.ReturnDiagnosticRegisterRequest,
        diag_msg.ChangeAsciiInputDelimiterRequest,
        diag_msg.ForceListenOnlyModeRequest,
        diag_msg.ClearCountersRequest,
        diag_msg.ReturnBusMessageCountRequest,
        diag_msg.ReturnBusCommunicationErrorCountRequest,
        diag_msg.ReturnBusExceptionErrorCountRequest,
        diag_msg.ReturnSlaveMessageCountRequest,
        diag_msg.ReturnSlaveNoResponseCountRequest,
        diag_msg.ReturnSlaveNAKCountRequest,
        diag_msg.ReturnSlaveBusyCountRequest,
        diag_msg.ReturnSlaveBusCharacterOverrunCountRequest,
        diag_msg.ReturnIopOverrunCountRequest,
        diag_msg.ClearOverrunCountRequest,
        diag_msg.GetClearModbusPlusRequest,
        mei_msg.ReadDeviceInformationRequest,
    ]

    @classmethod
    def getFCdict(cls) -> Dict[int, Callable]:
        """Build function code - class list."""
        return {f.function_code: f for f in cls.__function_table}  # type: ignore[attr-defined]

    def __init__(self) -> None:
        """Initialize the client lookup tables."""
        functions = {f.function_code for f in self.__function_table}  # type: ignore[attr-defined]
        self.lookup = self.getFCdict()
        self.__sub_lookup: Dict[int, Dict[int, Callable]] = {f: {} for f in functions}
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f  # type: ignore[attr-defined]

    def decode(self, message):
        """Decode a request packet.

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
        return self.lookup.get(function_code, pdu.ExceptionResponse)

    def _helper(self, data: str):
        """Generate the correct request object from a valid request packet.

        This decodes from a list of the currently implemented request types.

        :param data: The request packet to decode
        :returns: The decoded request or illegal function request object
        """
        function_code = int(data[0])
        if not (request := self.lookup.get(function_code, lambda: None)()):
            Log.debug("Factory Request[{}]", function_code)
            request = pdu.IllegalFunctionRequest(function_code)
        else:
            fc_string = "{}: {}".format(  # pylint: disable=consider-using-f-string
                str(self.lookup[function_code])  # pylint: disable=use-maxsplit-arg
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

    def register(self, function):
        """Register a function and sub function class with the decoder.

        :param function: Custom function class to register
        :raises MessageRegisterException:
        """
        if not issubclass(function, pdu.ModbusRequest):
            raise MessageRegisterException(
                f'"{function.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from "
                "`pymodbus.pdu.ModbusRequest` "
            )
        self.lookup[function.function_code] = function
        if hasattr(function, "sub_function_code"):
            if function.function_code not in self.__sub_lookup:
                self.__sub_lookup[function.function_code] = {}
            self.__sub_lookup[function.function_code][
                function.sub_function_code
            ] = function


# --------------------------------------------------------------------------- #
# Client Decoder
# --------------------------------------------------------------------------- #
class ClientDecoder:
    """Response Message Factory (Client).

    To add more implemented functions, simply add them to the list
    """

    function_table = [
        reg_r_msg.ReadHoldingRegistersResponse,
        bit_r_msg.ReadDiscreteInputsResponse,
        reg_r_msg.ReadInputRegistersResponse,
        bit_r_msg.ReadCoilsResponse,
        bit_w_msg.WriteMultipleCoilsResponse,
        reg_w_msg.WriteMultipleRegistersResponse,
        reg_w_msg.WriteSingleRegisterResponse,
        bit_w_msg.WriteSingleCoilResponse,
        reg_r_msg.ReadWriteMultipleRegistersResponse,
        diag_msg.DiagnosticStatusResponse,
        o_msg.ReadExceptionStatusResponse,
        o_msg.GetCommEventCounterResponse,
        o_msg.GetCommEventLogResponse,
        o_msg.ReportSlaveIdResponse,
        file_msg.ReadFileRecordResponse,
        file_msg.WriteFileRecordResponse,
        reg_w_msg.MaskWriteRegisterResponse,
        file_msg.ReadFifoQueueResponse,
        mei_msg.ReadDeviceInformationResponse,
    ]
    __sub_function_table = [
        diag_msg.ReturnQueryDataResponse,
        diag_msg.RestartCommunicationsOptionResponse,
        diag_msg.ReturnDiagnosticRegisterResponse,
        diag_msg.ChangeAsciiInputDelimiterResponse,
        diag_msg.ForceListenOnlyModeResponse,
        diag_msg.ClearCountersResponse,
        diag_msg.ReturnBusMessageCountResponse,
        diag_msg.ReturnBusCommunicationErrorCountResponse,
        diag_msg.ReturnBusExceptionErrorCountResponse,
        diag_msg.ReturnSlaveMessageCountResponse,
        diag_msg.ReturnSlaveNoResponseCountResponse,
        diag_msg.ReturnSlaveNAKCountResponse,
        diag_msg.ReturnSlaveBusyCountResponse,
        diag_msg.ReturnSlaveBusCharacterOverrunCountResponse,
        diag_msg.ReturnIopOverrunCountResponse,
        diag_msg.ClearOverrunCountResponse,
        diag_msg.GetClearModbusPlusResponse,
        mei_msg.ReadDeviceInformationResponse,
    ]

    def __init__(self) -> None:
        """Initialize the client lookup tables."""
        functions = {f.function_code for f in self.function_table}  # type: ignore[attr-defined]
        self.lookup = {f.function_code: f for f in self.function_table}  # type: ignore[attr-defined]
        self.__sub_lookup: Dict[int, Dict[int, Callable]] = {f: {} for f in functions}
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f  # type: ignore[attr-defined]

    def lookupPduClass(self, function_code):
        """Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        """
        return self.lookup.get(function_code, pdu.ExceptionResponse)

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

    def _helper(self, data: str):
        """Generate the correct response object from a valid response packet.

        This decodes from a list of the currently implemented request types.

        :param data: The response packet to decode
        :returns: The decoded request or an exception response object
        :raises ModbusException:
        """
        fc_string = data[0]
        function_code = int(fc_string)
        if function_code in self.lookup:  # pylint: disable=consider-using-assignment-expr
            fc_string = "{}: {}".format(  # pylint: disable=consider-using-f-string
                str(self.lookup[function_code])  # pylint: disable=use-maxsplit-arg
                .split(".")[-1]
                .rstrip('">"'),
                function_code,
            )
        Log.debug("Factory Response[{}]", fc_string)
        response = self.lookup.get(function_code, lambda: None)()
        if function_code > 0x80:
            code = function_code & 0x7F  # strip error portion
            response = pdu.ExceptionResponse(code, pdu.ModbusExceptions.IllegalFunction)
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
        if function and not issubclass(function, pdu.ModbusResponse):
            raise MessageRegisterException(
                f'"{function.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from "
                "`pymodbus.pdu.ModbusResponse` "
            )
        self.lookup[function.function_code] = function
        if hasattr(function, "sub_function_code"):
            if function.function_code not in self.__sub_lookup:
                self.__sub_lookup[function.function_code] = {}
            self.__sub_lookup[function.function_code][
                function.sub_function_code
            ] = function
