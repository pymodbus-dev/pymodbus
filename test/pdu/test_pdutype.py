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
        (bit_r_msg.ReadCoilsRequest, {"address": 117, "count": 3}, b''),
        (bit_r_msg.ReadDiscreteInputsRequest, {"address": 117, "count": 3}, b''),
        (bit_w_msg.WriteSingleCoilRequest, {"address": 117, "value": True}, b''),
        (bit_w_msg.WriteMultipleCoilsRequest, {"address": 117, "values": [True, False, True]}, b''),
        (diag_msg.DiagnosticStatusRequest, {}, b''),
        (diag_msg.DiagnosticStatusSimpleRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnQueryDataRequest, {"message": b'\x10\x01'}, b''),
        (diag_msg.RestartCommunicationsOptionRequest, {"toggle": True}, b''),
        (diag_msg.ReturnDiagnosticRegisterRequest, {"data": 0x1010}, b''),
        (diag_msg.ChangeAsciiInputDelimiterRequest, {"data": 0x1010}, b''),
        (diag_msg.ForceListenOnlyModeRequest, {}, b''),
        (diag_msg.ClearCountersRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnBusMessageCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnBusCommunicationErrorCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnBusExceptionErrorCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveMessageCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveNoResponseCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveNAKCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveBusyCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ReturnIopOverrunCountRequest, {"data": 0x1010}, b''),
        (diag_msg.ClearOverrunCountRequest, {"data": 0x1010}, b''),
        (diag_msg.GetClearModbusPlusRequest, {"data": 0x1010}, b''),
        (file_msg.ReadFileRecordRequest, {"records": [file_msg.FileRecord(), file_msg.FileRecord()]}, b''),
        (file_msg.WriteFileRecordRequest, {"records": [file_msg.FileRecord(), file_msg.FileRecord()]}, b''),
        (file_msg.ReadFifoQueueRequest, {"address": 117}, b''),
        (mei_msg.ReadDeviceInformationRequest, {"read_code": 0x17, "object_id": 0x29}, b''),
        (o_msg.ReadExceptionStatusRequest, {}, b''),
        (o_msg.GetCommEventCounterRequest, {}, b''),
        (o_msg.GetCommEventLogRequest, {}, b''),
        (o_msg.ReportSlaveIdRequest, {}, b''),
        (reg_r_msg.ReadHoldingRegistersRequest, {"address": 117, "count": 3}, b''),
        (reg_r_msg.ReadInputRegistersRequest, {"address": 117, "count": 3}, b''),
        (reg_r_msg.ReadWriteMultipleRegistersRequest, {"read_address": 17, "read_count": 2, "write_address": 25, "write_registers": [111, 112]}, b''),
        (reg_w_msg.WriteMultipleRegistersRequest, {"address": 117, "values": [111, 121, 131]}, b''),
        (reg_w_msg.WriteSingleRegisterRequest, {"address": 117, "value": 112}, b''),
        (reg_w_msg.MaskWriteRegisterRequest, {"address": 0x0104, "and_mask": 0xE1D2, "or_mask": 0x1234}, b''),
    ]

    responses = [
        (bit_r_msg.ReadCoilsResponse, {"values": [3, 17]}, b''),
        (bit_r_msg.ReadDiscreteInputsResponse, {"values": [3, 17]}, b''),
        (bit_w_msg.WriteSingleCoilResponse, {"address": 117, "value": True}, b''),
        (bit_w_msg.WriteMultipleCoilsResponse, {"address": 117, "count": 3}, b''),
        (diag_msg.DiagnosticStatusResponse, {}, b''),
        (diag_msg.DiagnosticStatusSimpleResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnQueryDataResponse, {"message": b'AB'}, b''),
        (diag_msg.RestartCommunicationsOptionResponse, {"toggle": True}, b''),
        (diag_msg.ReturnDiagnosticRegisterResponse, {"data": 0x1010}, b''),
        (diag_msg.ChangeAsciiInputDelimiterResponse, {"data": 0x1010}, b''),
        (diag_msg.ForceListenOnlyModeResponse, {}, b''),
        (diag_msg.ClearCountersResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnBusMessageCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnBusCommunicationErrorCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnBusExceptionErrorCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveMessageCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveNoResponseCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveNAKCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveBusyCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ReturnIopOverrunCountResponse, {"data": 0x1010}, b''),
        (diag_msg.ClearOverrunCountResponse, {"data": 0x1010}, b''),
        (diag_msg.GetClearModbusPlusResponse, {"data": 0x1010}, b''),
        (file_msg.ReadFileRecordResponse, {"records": [file_msg.FileRecord(), file_msg.FileRecord()]}, b''),
        (file_msg.WriteFileRecordResponse, {"records": [file_msg.FileRecord(), file_msg.FileRecord()]}, b''),
        (file_msg.ReadFifoQueueResponse, {"values": [123, 456]}, b''),
        (mei_msg.ReadDeviceInformationResponse, {"read_code": 0x17}, b''),
        (o_msg.ReadExceptionStatusResponse, {"status": 0x23}, b''),
        (o_msg.GetCommEventCounterResponse, {"count": 123}, b''),
        (o_msg.GetCommEventLogResponse, {"status": True, "message_count": 12, "event_count": 7, "events": [12, 14]}, b''),
        (o_msg.ReportSlaveIdResponse, {"identifier": b'\x12', "status": True}, b''),
        (reg_r_msg.ReadHoldingRegistersResponse, {"values": [3, 17]}, b''),
        (reg_r_msg.ReadInputRegistersResponse, {"values": [3, 17]}, b''),
        (reg_r_msg.ReadWriteMultipleRegistersResponse, {"values": [1, 2]}, b''),
        (reg_w_msg.WriteSingleRegisterResponse, {"address": 117, "value": 112}, b''),
        (reg_w_msg.WriteMultipleRegistersResponse, {"address": 117, "count": 3}, b''),
        (reg_w_msg.MaskWriteRegisterResponse, {"address": 0x0104, "and_mask": 0xE1D2, "or_mask": 0x1234}, b''),
    ]


    @pytest.mark.parametrize(("pdutype", "kwargs", "framer"), requests)
    @pytest.mark.usefixtures("kwargs", "framer")
    def test_pdu_instance(self, pdutype):
        """Test that all PDU types can be created."""
        pdu = pdutype()
        assert pdu
        assert str(pdu)

    @pytest.mark.parametrize(("pdutype", "kwargs", "framer"), requests + responses)
    @pytest.mark.usefixtures("framer")
    def test_pdu_instance_args(self, pdutype, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(**kwargs)
        assert pdu
        assert str(pdu)

    @pytest.mark.parametrize(("pdutype", "kwargs", "framer"), requests + responses)
    @pytest.mark.usefixtures("framer")
    def test_pdu_instance_encode(self, pdutype, kwargs):
        """Test that all PDU types can be created."""
        pdutype(**kwargs).encode()
        # Fix Check frame against test case

    @pytest.mark.parametrize(("pdutype", "kwargs", "framer"), requests + responses)
    @pytest.mark.usefixtures("framer")
    def test_pdu_special_methods(self, pdutype, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(**kwargs)
        if hasattr(pdu, "get_response_pdu_size"):
            pdu.get_response_pdu_size()
        if hasattr(pdu, "setBit"):
            pdu.setBit(0)
        if hasattr(pdu, "resetBit"):
            pdu.resetBit(0)
        if hasattr(pdu, "getBit"):
            pdu.getBit(0)
