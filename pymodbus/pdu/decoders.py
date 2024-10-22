"""Modbus Request/Response Decoders."""
from __future__ import annotations

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

    _pdu_class_table: set[tuple[type[base.ModbusPDU], type[base.ModbusPDU]]] = {
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

    _pdu_sub_class_table: set[tuple[type[base.ModbusPDU], type[base.ModbusPDU]]] = {
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
    }

    def __init__(self, is_server: bool) -> None:
        """Initialize function_tables."""
        inx = 0 if is_server else 1
        self.lookup: dict[int, type[base.ModbusPDU]] = {cl[inx].function_code: cl[inx] for cl in self._pdu_class_table}
        self.sub_lookup: dict[int, dict[int, type[base.ModbusPDU]]] = {f: {} for f in self.lookup}
        for f in self._pdu_sub_class_table:
            self.sub_lookup[f[inx].function_code][f[inx].sub_function_code] = f[inx]

    def lookupPduClass(self, function_code: int) -> type[base.ModbusPDU]:
        """Use `function_code` to determine the class of the PDU."""
        return self.lookup.get(function_code, base.ExceptionResponse)

    def register(self, custom_class: type[base.ModbusPDU]) -> None:
        """Register a function and sub function class with the decoder."""
        if not issubclass(custom_class, base.ModbusPDU):
            raise MessageRegisterException(
                f'"{custom_class.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from "
                "`pymodbus.pdu.ModbusPDU` "
            )
        self.lookup[custom_class.function_code] = custom_class
        if custom_class.sub_function_code >= 0:
            if custom_class.function_code not in self.sub_lookup:
                self.sub_lookup[custom_class.function_code] = {}
            self.sub_lookup[custom_class.function_code][
                custom_class.sub_function_code
            ] = custom_class

    def decode(self, frame: bytes) -> base.ModbusPDU | None:
        """Decode a frame."""
        try:
            if (function_code := int(frame[0])) > 0x80:
                pdu_exp = base.ExceptionResponse(function_code & 0x7F)
                pdu_exp.decode(frame[1:])
                return pdu_exp
            if not (pdu_type := self.lookup.get(function_code, None)):
                Log.debug("decode PDU failed for function code {}", function_code)
                raise ModbusException(f"Unknown response {function_code}")
            pdu = pdu_type()
            pdu.setData(0, 0, False)
            Log.debug("decode PDU for {}", function_code)
            pdu.decode(frame[1:])

            if pdu.sub_function_code >= 0:
                lookup = self.sub_lookup.get(pdu.function_code, {})
                if subtype := lookup.get(pdu.sub_function_code, None):
                    pdu.__class__ = subtype
            return pdu
        except (ModbusException, ValueError, IndexError) as exc:
            Log.warning("Unable to decode frame {}", exc)
        return None
