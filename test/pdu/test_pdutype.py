"""Test pdu."""
import pytest

import pymodbus.pdu.bit_read_message as bit_r_msg
import pymodbus.pdu.bit_write_message as bit_w_msg
import pymodbus.pdu.diag_message as diag_msg
import pymodbus.pdu.file_message as file_msg
import pymodbus.pdu.mei_message as mei_msg
import pymodbus.pdu.other_message as o_msg
import pymodbus.pdu.register_read_message as reg_r_msg
import pymodbus.pdu.register_write_message as reg_w_msg


class TestPduType:
    """Test all PDU types requests/responses."""

    requests = [
        (bit_r_msg.ReadCoilsRequest, {"address": 117, "count": 3}),
        (bit_r_msg.ReadDiscreteInputsRequest, {"address": 117, "count": 3}),
        (bit_w_msg.WriteSingleCoilRequest, {"address": 117, "value": True}),
        (bit_w_msg.WriteMultipleCoilsRequest, {"address": 117, "values": [True, False, True]}),
        (diag_msg.DiagnosticStatusRequest, {}),
        (diag_msg.DiagnosticStatusSimpleRequest, {"data": 0x1010}),
        (diag_msg.ReturnQueryDataRequest, {"message": b'\x10\x01'}),
        (diag_msg.RestartCommunicationsOptionRequest, {"toggle": True}),
        (diag_msg.ReturnDiagnosticRegisterRequest, {"data": 0x1010}),
        (diag_msg.ChangeAsciiInputDelimiterRequest, {"data": 0x1010}),
        (diag_msg.ForceListenOnlyModeRequest, {}),
        (diag_msg.ClearCountersRequest, {"data": 0x1010}),
        (diag_msg.ReturnBusMessageCountRequest, {"data": 0x1010}),
        (diag_msg.ReturnBusCommunicationErrorCountRequest, {"data": 0x1010}),
        (diag_msg.ReturnBusExceptionErrorCountRequest, {"data": 0x1010}),
        (diag_msg.ReturnSlaveMessageCountRequest, {"data": 0x1010}),
        (diag_msg.ReturnSlaveNoResponseCountRequest, {"data": 0x1010}),
        (diag_msg.ReturnSlaveNAKCountRequest, {"data": 0x1010}),
        (diag_msg.ReturnSlaveBusyCountRequest, {"data": 0x1010}),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountRequest, {"data": 0x1010}),
        (diag_msg.ReturnIopOverrunCountRequest, {"data": 0x1010}),
        (diag_msg.ClearOverrunCountRequest, {"data": 0x1010}),
        (diag_msg.GetClearModbusPlusRequest, {"data": 0x1010}),
        (file_msg.ReadFileRecordRequest, {"records": [117, 119]}),
        (file_msg.WriteFileRecordRequest, {"records": [b'123', b'456']}),
        (file_msg.ReadFifoQueueRequest, {"address": 117}),
        (mei_msg.ReadDeviceInformationRequest, {"read_code": 0x17, "object_id": 0x29}),

        (reg_r_msg.ReadHoldingRegistersRequest, {}),
        (reg_r_msg.ReadInputRegistersRequest, {}),
        (reg_w_msg.WriteMultipleRegistersRequest, {}),
        (reg_w_msg.WriteSingleRegisterRequest, {}),
        (reg_r_msg.ReadWriteMultipleRegistersRequest, {}),
        (o_msg.ReadExceptionStatusRequest, {}),
        (o_msg.GetCommEventCounterRequest, {}),
        (o_msg.GetCommEventLogRequest, {}),
        (o_msg.ReportSlaveIdRequest, {}),
        (reg_w_msg.MaskWriteRegisterRequest, {}),
    ]

    responses = [
        (bit_r_msg.ReadCoilsResponse, {"values": [3, 17]}),
        (bit_r_msg.ReadDiscreteInputsResponse, {"values": [3, 17]}),
        (bit_w_msg.WriteSingleCoilResponse, {"address": 117, "value": True}),
        (bit_w_msg.WriteMultipleCoilsResponse, {"address": 117, "count": 3}),
        (diag_msg.DiagnosticStatusResponse, {}),
        (diag_msg.DiagnosticStatusSimpleResponse, {"data": 0x1010}),
        (diag_msg.ReturnQueryDataResponse, {"message": b'AB'}),
        (diag_msg.RestartCommunicationsOptionResponse, {"toggle": True}),
        (diag_msg.ReturnDiagnosticRegisterResponse, {"data": 0x1010}),
        (diag_msg.ChangeAsciiInputDelimiterResponse, {"data": 0x1010}),
        (diag_msg.ForceListenOnlyModeResponse, {}),
        (diag_msg.ClearCountersResponse, {"data": 0x1010}),
        (diag_msg.ReturnBusMessageCountResponse, {"data": 0x1010}),
        (diag_msg.ReturnBusCommunicationErrorCountResponse, {"data": 0x1010}),
        (diag_msg.ReturnBusExceptionErrorCountResponse, {"data": 0x1010}),
        (diag_msg.ReturnSlaveMessageCountResponse, {"data": 0x1010}),
        (diag_msg.ReturnSlaveNoResponseCountResponse, {"data": 0x1010}),
        (diag_msg.ReturnSlaveNAKCountResponse, {"data": 0x1010}),
        (diag_msg.ReturnSlaveBusyCountResponse, {"data": 0x1010}),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountResponse, {"data": 0x1010}),
        (diag_msg.ReturnIopOverrunCountResponse, {"data": 0x1010}),
        (diag_msg.ClearOverrunCountResponse, {"data": 0x1010}),
        (diag_msg.GetClearModbusPlusResponse, {"data": 0x1010}),
        (file_msg.ReadFileRecordResponse, {"records": [b'123', b'456']}),
        (file_msg.WriteFileRecordResponse, {"records": [b'123', b'456']}),
        (file_msg.ReadFifoQueueResponse, {"values": [b'123', b'456']}),
        (mei_msg.ReadDeviceInformationResponse, {"read_code": 0x17, "information": 0x29}),

        (reg_r_msg.ReadHoldingRegistersResponse, {}),
        (reg_r_msg.ReadInputRegistersResponse, {}),
        (reg_w_msg.WriteSingleRegisterResponse, {}),
        (reg_w_msg.WriteMultipleRegistersResponse, {}),
        (reg_r_msg.ReadWriteMultipleRegistersResponse, {}),
        (o_msg.ReadExceptionStatusResponse, {}),
        (o_msg.GetCommEventCounterResponse, {}),
        (o_msg.GetCommEventLogResponse, {}),
        (o_msg.ReportSlaveIdResponse, {}),
        (reg_w_msg.MaskWriteRegisterResponse, {}),
    ]


    @pytest.mark.parametrize(("pdutype", "_kwargs"), requests + responses)
    def xtest_pdu_instance(self, pdutype, _kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype()
        assert pdu
        assert str(pdu)

    @pytest.mark.parametrize(("pdutype", "kwargs"), requests + responses)
    def test_pdu_instance_args(self, pdutype, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(**kwargs)
        assert pdu
        assert str(pdu)
