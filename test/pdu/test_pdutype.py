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


class TestPduType:  # pylint: disable=too-few-public-methods
    """Test all PDU types requests/responses."""

    requests = [
        (bit_r_msg.ReadCoilsRequest, {"address": 117, "count": 3}),
        (bit_r_msg.ReadDiscreteInputsRequest, {"address": 117, "count": 3}),
        (bit_w_msg.WriteSingleCoilRequest, {"address": 117, "value": True}),
        (bit_w_msg.WriteMultipleCoilsRequest, {"address": 117, "value": [True, False, True]}),

        (reg_r_msg.ReadHoldingRegistersRequest, ()),
        (reg_r_msg.ReadInputRegistersRequest, ()),
        (reg_w_msg.WriteMultipleRegistersRequest, ()),
        (reg_w_msg.WriteSingleRegisterRequest, ()),
        (reg_r_msg.ReadWriteMultipleRegistersRequest, ()),
        (diag_msg.DiagnosticStatusRequest, ()),
        (o_msg.ReadExceptionStatusRequest, ()),
        (o_msg.GetCommEventCounterRequest, ()),
        (o_msg.GetCommEventLogRequest, ()),
        (o_msg.ReportSlaveIdRequest, ()),
        (file_msg.ReadFileRecordRequest, ()),
        (file_msg.WriteFileRecordRequest, ()),
        (reg_w_msg.MaskWriteRegisterRequest, ()),
        (file_msg.ReadFifoQueueRequest, ()),
        (mei_msg.ReadDeviceInformationRequest, ()),
        (diag_msg.ReturnQueryDataRequest, ()),
        (diag_msg.RestartCommunicationsOptionRequest, ()),
        (diag_msg.ReturnDiagnosticRegisterRequest, ()),
        (diag_msg.ChangeAsciiInputDelimiterRequest, ()),
        (diag_msg.ForceListenOnlyModeRequest, ()),
        (diag_msg.ClearCountersRequest, ()),
        (diag_msg.ReturnBusMessageCountRequest, ()),
        (diag_msg.ReturnBusCommunicationErrorCountRequest, ()),
        (diag_msg.ReturnBusExceptionErrorCountRequest, ()),
        (diag_msg.ReturnSlaveMessageCountRequest, ()),
        (diag_msg.ReturnSlaveNoResponseCountRequest, ()),
        (diag_msg.ReturnSlaveNAKCountRequest, ()),
        (diag_msg.ReturnSlaveBusyCountRequest, ()),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountRequest, ()),
        (diag_msg.ReturnIopOverrunCountRequest, ()),
        (diag_msg.ClearOverrunCountRequest, ()),
        (diag_msg.GetClearModbusPlusRequest, ()),
        (mei_msg.ReadDeviceInformationRequest, ()),
    ]

    responses = [
        (bit_r_msg.ReadCoilsResponse, {"values": [3, 17]}),
        (bit_r_msg.ReadDiscreteInputsResponse, {"values": [3, 17]}),
        (bit_w_msg.WriteSingleCoilResponse, {"address": 117, "value": True}),
        (bit_w_msg.WriteMultipleCoilsResponse, {"address": 117, "count": 3}),

        (reg_r_msg.ReadHoldingRegistersResponse, ()),
        (reg_r_msg.ReadInputRegistersResponse, ()),
        (reg_w_msg.WriteSingleRegisterResponse, ()),
        (reg_w_msg.WriteMultipleRegistersResponse, ()),
        (reg_r_msg.ReadWriteMultipleRegistersResponse, ()),
        (diag_msg.DiagnosticStatusResponse, ()),
        (o_msg.ReadExceptionStatusResponse, ()),
        (o_msg.GetCommEventCounterResponse, ()),
        (o_msg.GetCommEventLogResponse, ()),
        (o_msg.ReportSlaveIdResponse, ()),
        (file_msg.ReadFileRecordResponse, ()),
        (file_msg.WriteFileRecordResponse, ()),
        (reg_w_msg.MaskWriteRegisterResponse, ()),
        (file_msg.ReadFifoQueueResponse, ()),
        (mei_msg.ReadDeviceInformationResponse, ()),
        (diag_msg.ReturnQueryDataResponse, ()),
        (diag_msg.RestartCommunicationsOptionResponse, ()),
        (diag_msg.ReturnDiagnosticRegisterResponse, ()),
        (diag_msg.ChangeAsciiInputDelimiterResponse, ()),
        (diag_msg.ForceListenOnlyModeResponse, ()),
        (diag_msg.ClearCountersResponse, ()),
        (diag_msg.ReturnBusMessageCountResponse, ()),
        (diag_msg.ReturnBusCommunicationErrorCountResponse, ()),
        (diag_msg.ReturnBusExceptionErrorCountResponse, ()),
        (diag_msg.ReturnSlaveMessageCountResponse, ()),
        (diag_msg.ReturnSlaveNoResponseCountResponse, ()),
        (diag_msg.ReturnSlaveNAKCountResponse, ()),
        (diag_msg.ReturnSlaveBusyCountResponse, ()),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountResponse, ()),
        (diag_msg.ReturnIopOverrunCountResponse, ()),
        (diag_msg.ClearOverrunCountResponse, ()),
        (diag_msg.GetClearModbusPlusResponse, ()),
        (mei_msg.ReadDeviceInformationResponse, ()),
    ]


    @pytest.mark.parametrize(("pdutype", "args"), requests + responses)
    def test_pdu_instance(self, pdutype, args):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args)
        assert pdu
        assert str(pdu)
