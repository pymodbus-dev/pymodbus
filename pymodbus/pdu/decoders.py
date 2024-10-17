"""Modbus Request/Response Decoders."""
from collections.abc import Callable

import pymodbus.pdu.bit_read_message as bit_r_msg
import pymodbus.pdu.bit_write_message as bit_w_msg
import pymodbus.pdu.diag_message as diag_msg
import pymodbus.pdu.file_message as file_msg
import pymodbus.pdu.mei_message as mei_msg
import pymodbus.pdu.other_message as o_msg
import pymodbus.pdu.pdu as base
import pymodbus.pdu.register_read_message as reg_r_msg
import pymodbus.pdu.register_write_message as reg_w_msg
from pymodbus.exceptions import MessageRegisterException, ModbusException
from pymodbus.logging import Log


class DecodePDU:
    """Decode pdu requests/responses (server/client)."""

    _pdu_class_table = {
        (reg_r_msg.ReadHoldingRegistersRequest, reg_r_msg.ReadHoldingRegistersResponse),
        (bit_r_msg.ReadDiscreteInputsRequest, bit_r_msg.ReadDiscreteInputsResponse),
        (reg_r_msg.ReadInputRegistersRequest, reg_r_msg.ReadInputRegistersResponse),
        (bit_r_msg.ReadCoilsRequest, bit_r_msg.ReadCoilsResponse),
        (bit_w_msg.WriteMultipleCoilsRequest, bit_w_msg.WriteMultipleCoilsResponse),
        (reg_w_msg.WriteMultipleRegistersRequest, reg_w_msg.WriteMultipleRegistersResponse),
        (reg_w_msg.WriteSingleRegisterRequest, reg_w_msg.WriteSingleRegisterResponse),
        (bit_w_msg.WriteSingleCoilRequest, bit_w_msg.WriteSingleCoilResponse),
        (reg_r_msg.ReadWriteMultipleRegistersRequest, reg_r_msg.ReadWriteMultipleRegistersResponse),
        (diag_msg.DiagnosticStatusRequest, diag_msg.DiagnosticStatusResponse),
        (o_msg.ReadExceptionStatusRequest, o_msg.ReadExceptionStatusResponse),
        (o_msg.GetCommEventCounterRequest, o_msg.GetCommEventCounterResponse),
        (o_msg.GetCommEventLogRequest, o_msg.GetCommEventLogResponse),
        (o_msg.ReportSlaveIdRequest, o_msg.ReportSlaveIdResponse),
        (file_msg.ReadFileRecordRequest, file_msg.ReadFileRecordResponse),
        (file_msg.WriteFileRecordRequest, file_msg.WriteFileRecordResponse),
        (reg_w_msg.MaskWriteRegisterRequest, reg_w_msg.MaskWriteRegisterResponse),
        (file_msg.ReadFifoQueueRequest, file_msg.ReadFifoQueueResponse),
        (mei_msg.ReadDeviceInformationRequest, mei_msg.ReadDeviceInformationResponse),
    }

    _pdu_sub_class_table = [
        (diag_msg.ReturnQueryDataRequest, diag_msg.ReturnQueryDataResponse),
        (diag_msg.RestartCommunicationsOptionRequest, diag_msg.RestartCommunicationsOptionResponse),
        (diag_msg.ReturnDiagnosticRegisterRequest, diag_msg.ReturnDiagnosticRegisterResponse),
        (diag_msg.ChangeAsciiInputDelimiterRequest, diag_msg.ChangeAsciiInputDelimiterResponse),
        (diag_msg.ForceListenOnlyModeRequest, diag_msg.ForceListenOnlyModeResponse),
        (diag_msg.ClearCountersRequest, diag_msg.ClearCountersResponse),
        (diag_msg.ReturnBusMessageCountRequest, diag_msg.ReturnBusMessageCountResponse),
        (diag_msg.ReturnBusCommunicationErrorCountRequest, diag_msg.ReturnBusCommunicationErrorCountResponse),
        (diag_msg.ReturnBusExceptionErrorCountRequest, diag_msg.ReturnBusExceptionErrorCountResponse),
        (diag_msg.ReturnSlaveMessageCountRequest, diag_msg.ReturnSlaveMessageCountResponse),
        (diag_msg.ReturnSlaveNoResponseCountRequest, diag_msg.ReturnSlaveNoResponseCountResponse),
        (diag_msg.ReturnSlaveNAKCountRequest, diag_msg.ReturnSlaveNAKCountResponse),
        (diag_msg.ReturnSlaveBusyCountRequest, diag_msg.ReturnSlaveBusyCountResponse),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountRequest, diag_msg.ReturnSlaveBusCharacterOverrunCountResponse),
        (diag_msg.ReturnIopOverrunCountRequest, diag_msg.ReturnIopOverrunCountResponse),
        (diag_msg.ClearOverrunCountRequest, diag_msg.ClearOverrunCountResponse),
        (diag_msg.GetClearModbusPlusRequest, diag_msg.GetClearModbusPlusResponse),
        (mei_msg.ReadDeviceInformationRequest, mei_msg.ReadDeviceInformationResponse),
    ]

    def __init__(self, is_server: bool) -> None:
        """Initialize function_tables."""
        inx = 1 if is_server else 0
        self.lookup: dict[int, Callable] = {cl[inx].function_code: cl[inx] for cl in self._pdu_class_table}  # type: ignore[attr-defined]
        self.sub_lookup: dict[int, dict[int, Callable]] = {f: {} for f in self.lookup}
        for f in self._pdu_sub_class_table:
            self.sub_lookup[f[inx].function_code][f[inx].sub_function_code] = f[inx]  # type: ignore[attr-defined]

    def lookupPduClass(self, function_code):
        """Use `function_code` to determine the class of the PDU."""
        return self.lookup.get(function_code, base.ExceptionResponse)

    def register(self, function):
        """Register a function and sub function class with the decoder."""
        if not issubclass(function, base.ModbusPDU):
            raise MessageRegisterException(
                f'"{function.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from "
                "`pymodbus.pdu.ModbusPDU` "
            )
        self.lookup[function.function_code] = function
        if hasattr(function, "sub_function_code"):
            if function.function_code not in self.sub_lookup:
                self.sub_lookup[function.function_code] = {}
            self.sub_lookup[function.function_code][
                function.sub_function_code
            ] = function

    def decode(self, frame):
        """Decode a frame."""
        try:
            if (function_code := int(frame[0])) > 0x80:
                pdu = base.ExceptionResponse(function_code & 0x7F)
                pdu.decode(frame[1:])
                return pdu
            return self._helper(frame, function_code)
        except ModbusException as exc:
            Log.warning("Unable to decode frame {}", exc)
        return None

    def _helper(self, data: str, function_code):
        """Generate the correct object from a valid frame."""



# --------------------------------------------------------------------------- #
# Server Decoder
# --------------------------------------------------------------------------- #
class DecoderRequests(DecodePDU):
    """Decode request Message (Server)."""

    def __init__(self) -> None:
        """Initialize the client lookup tables."""
        super().__init__(False)

    def _helper(self, data: str, function_code):
        """Generate the correct request object from a valid request packet."""
        if not (request := self.lookup.get(function_code, lambda: None)()):
            Log.debug("decode PDU failed for function code {}", function_code)
            request = base.ExceptionResponse(
                function_code,
                exception_code=base.ModbusExceptions.IllegalFunction
            )
        else:
            fc_string = "{}: {}".format(  # pylint: disable=consider-using-f-string
                str(self.lookup[function_code])  # pylint: disable=use-maxsplit-arg
                .split(".")[-1]
                .rstrip('">"'),
                function_code,
            )
            Log.debug("decode PDU for {}", fc_string)
        request.decode(data[1:])

        if hasattr(request, "sub_function_code"):
            lookup = self.sub_lookup.get(request.function_code, {})
            if subtype := lookup.get(request.sub_function_code, None):
                request.__class__ = subtype

        return request

# --------------------------------------------------------------------------- #
# Client Decoder
# --------------------------------------------------------------------------- #
class DecoderResponses(DecodePDU):
    """Response Message Factory (Client).

    To add more implemented functions, simply add them to the list
    """

    def __init__(self) -> None:
        """Initialize the client lookup tables."""
        super().__init__(True)

    def _helper(self, data: str, function_code):
        """Generate the correct response object from a valid response packet."""
        if function_code in self.lookup:
            fc_string = "{}: {}".format(  # pylint: disable=consider-using-f-string
                str(self.lookup[function_code])  # pylint: disable=use-maxsplit-arg
                .split(".")[-1]
                .rstrip('">"'),
                function_code,
            )
        else:
            fc_string = str(function_code)
        Log.debug("Factory Response[{}]", fc_string)
        response = self.lookup.get(function_code, lambda: None)()
        if function_code > 0x80:
            code = function_code & 0x7F  # strip error portion
            response = base.ExceptionResponse(code, exception_code=base.ModbusExceptions.IllegalFunction)
        if not response:
            raise ModbusException(f"Unknown response {function_code}")
        response.decode(data[1:])

        if hasattr(response, "sub_function_code"):
            lookup = self.sub_lookup.get(response.function_code, {})
            if subtype := lookup.get(response.sub_function_code, None):
                response.__class__ = subtype

        return response
