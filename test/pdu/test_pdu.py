"""Test pdu."""
import pytest

import pymodbus.pdu.bit_read_message as bit_r_msg
import pymodbus.pdu.diag_message as diag_msg
import pymodbus.pdu.file_message as file_msg
import pymodbus.pdu.mei_message as mei_msg
import pymodbus.pdu.other_message as o_msg
import pymodbus.pdu.register_read_message as reg_r_msg
import pymodbus.pdu.register_write_message as reg_w_msg
from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import (
    ExceptionResponse,
    ModbusExceptions,
    ModbusPDU,
)

from ..conftest import MockContext


class TestPdu:
    """Test modbus PDU."""

    exception = ExceptionResponse(1, 1, 0, 0, False)

    async def test_error_methods(self):
        """Test all error methods."""
        result = self.exception.encode()
        self.exception.decode(result)
        assert result == b"\x01"
        assert self.exception.exception_code == 1

    async def test_get_pdu_size(self):
        """Test get pdu size."""
        assert not self.exception.get_response_pdu_size()

    async def test_is_error(self):
        """Test is_error."""
        assert self.exception.isError()

    def test_request_exception(self):
        """Test request exception."""
        request = ModbusPDU()
        request.setBaseData(0, 0, False)
        request.function_code = 1
        errors = {ModbusExceptions.decode(c): c for c in range(1, 20)}
        for error, code in iter(errors.items()):
            result = request.doException(code)
            assert str(result) == f"Exception Response(129, 1, {error})"

    def test_calculate_rtu_frame_size(self):
        """Test the calculation of Modbus frame sizes."""
        with pytest.raises(NotImplementedException):
            ModbusPDU.calculateRtuFrameSize(b"")
        ModbusPDU._rtu_frame_size = 5  # pylint: disable=protected-access
        assert ModbusPDU.calculateRtuFrameSize(b"") == 5
        ModbusPDU._rtu_frame_size = None  # pylint: disable=protected-access
        ModbusPDU._rtu_byte_count_pos = 2  # pylint: disable=protected-access
        assert (
            ModbusPDU.calculateRtuFrameSize(
                b"\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"
            )
            == 0x05 + 5
        )
        assert not ModbusPDU.calculateRtuFrameSize(b"\x11")
        ModbusPDU._rtu_byte_count_pos = None  # pylint: disable=protected-access
        with pytest.raises(NotImplementedException):
            ModbusPDU.calculateRtuFrameSize(b"")
        ModbusPDU._rtu_frame_size = 12  # pylint: disable=protected-access
        assert ModbusPDU.calculateRtuFrameSize(b"") == 12
        ModbusPDU._rtu_frame_size = None  # pylint: disable=protected-access
        ModbusPDU._rtu_byte_count_pos = 2  # pylint: disable=protected-access
        assert (
            ModbusPDU.calculateRtuFrameSize(
                b"\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"
            )
            == 0x05 + 5
        )
        ModbusPDU._rtu_byte_count_pos = None  # pylint: disable=protected-access

    # --------------------------
    # Test PDU types generically
    # --------------------------

    requests = [
        (bit_r_msg.ReadCoilsRequest, (), {"address": 117, "count": 3}, b'\x01\x00\x75\x00\x03'),
        (bit_r_msg.ReadDiscreteInputsRequest, (), {"address": 117, "count": 3}, b'\x02\x00\x75\x00\x03'),
        (bit_r_msg.WriteSingleCoilRequest, (), {"address": 117, "value": True}, b'\x05\x00\x75\xff\x00'),
        (bit_r_msg.WriteMultipleCoilsRequest, (), {"address": 117, "values": [True, False, True]}, b'\x0f\x00\x75\x00\x03\x01\x05'),
        (diag_msg.DiagnosticStatusRequest, (), {}, b'\x08\x27\x0f'),
        (diag_msg.DiagnosticStatusSimpleRequest, (), {"data": 0x1010}, b'\x08\x27\x0f\x10\x10'),
        (diag_msg.ReturnQueryDataRequest, (), {"message": b'\x10\x01'}, b'\x08\x00\x00\x10\x01'),
        (diag_msg.RestartCommunicationsOptionRequest, (), {"toggle": True}, b'\x08\x00\x01\xff\x00'),
        (diag_msg.ReturnDiagnosticRegisterRequest, (), {"data": 0x1010}, b'\x08\x00\x02\x10\x10'),
        (diag_msg.ChangeAsciiInputDelimiterRequest, (), {"data": 0x1010}, b'\x08\x00\x03\x10\x10'),
        (diag_msg.ForceListenOnlyModeRequest, (), {}, b'\x08\x00\x04\x00\x00'),
        (diag_msg.ClearCountersRequest, (), {"data": 0x1010}, b'\x08\x00\n\x10\x10'),
        (diag_msg.ReturnBusMessageCountRequest, (), {"data": 0x1010}, b'\x08\x00\x0b\x10\x10'),
        (diag_msg.ReturnBusCommunicationErrorCountRequest, (), {"data": 0x1010}, b'\x08\x00\x0c\x10\x10'),
        (diag_msg.ReturnBusExceptionErrorCountRequest, (), {"data": 0x1010}, b'\x08\x00\x0d\x10\x10'),
        (diag_msg.ReturnSlaveMessageCountRequest, (), {"data": 0x1010}, b'\x08\x00\x0e\x10\x10'),
        (diag_msg.ReturnSlaveNoResponseCountRequest, (), {"data": 0x1010}, b'\x08\x00\x0f\x10\x10'),
        (diag_msg.ReturnSlaveNAKCountRequest, (), {"data": 0x1010}, b'\x08\x00\x10\x10\x10'),
        (diag_msg.ReturnSlaveBusyCountRequest, (), {"data": 0x1010}, b'\x08\x00\x11\x10\x10'),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountRequest, (), {"data": 0x1010}, b'\x08\x00\x12\x10\x10'),
        (diag_msg.ReturnIopOverrunCountRequest, (), {"data": 0x1010}, b'\x08\x00\x13\x10\x10'),
        (diag_msg.ClearOverrunCountRequest, (), {"data": 0x1010}, b'\x08\x00\x14\x10\x10'),
        (diag_msg.GetClearModbusPlusRequest, (), {"data": 0x1010}, b'\x08\x00\x15\x10\x10'),
        (file_msg.ReadFileRecordRequest, (), {"records": [file_msg.FileRecord(), file_msg.FileRecord()]}, b'\x14\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00'),
        (file_msg.WriteFileRecordRequest, (), {"records": [file_msg.FileRecord(), file_msg.FileRecord()]}, b'\x15\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00'),
        (file_msg.ReadFifoQueueRequest, (), {"address": 117}, b'\x18\x00\x75'),
        (mei_msg.ReadDeviceInformationRequest, (), {"read_code": 0x17, "object_id": 0x29}, b'\x2b\x0e\x17\x29'),
        (o_msg.ReadExceptionStatusRequest, (), {}, b'\x07'),
        (o_msg.GetCommEventCounterRequest, (), {}, b'\x0b'),
        (o_msg.GetCommEventLogRequest, (), {}, b'\x0c'),
        (o_msg.ReportSlaveIdRequest, (), {}, b'\x11'),
        (reg_r_msg.ReadHoldingRegistersRequest, (), {"address": 117, "count": 3}, b'\x03\x00\x75\x00\x03'),
        (reg_r_msg.ReadInputRegistersRequest, (), {"address": 117, "count": 3}, b'\x04\x00\x75\x00\x03'),
        (reg_r_msg.ReadWriteMultipleRegistersRequest, (), {"read_address": 17, "read_count": 2, "write_address": 25, "write_registers": [111, 112]}, b'\x17\x00\x11\x00\x02\x00\x19\x00\x02\x04\x00\x6f\x00\x70'),
        (reg_w_msg.WriteMultipleRegistersRequest, (), {"address": 117, "values": [111, 121, 131]}, b'\x10\x00\x75\x00\x03\x06\x00\x6f\x00\x79\x00\x83'),
        (reg_w_msg.WriteSingleRegisterRequest, (), {"address": 117, "value": 112}, b'\x06\x00\x75\x00\x70'),
        (reg_w_msg.MaskWriteRegisterRequest, (), {"address": 0x0104, "and_mask": 0xE1D2, "or_mask": 0x1234}, b'\x16\x01\x04\xe1\xd2\x12\x34'),
    ]

    responses = [
        (bit_r_msg.ReadCoilsResponse, (), {"values": [3, 17]}, b'\x01\x01\x03'),
        (bit_r_msg.ReadDiscreteInputsResponse, (), {"values": [3, 17]}, b'\x02\x01\x03'),
        (bit_r_msg.WriteSingleCoilResponse, (), {"address": 117, "value": True}, b'\x05\x00\x75\xff\x00'),
        (bit_r_msg.WriteMultipleCoilsResponse, (), {"address": 117, "count": 3}, b'\x0f\x00\x75\x00\x03'),
        (diag_msg.DiagnosticStatusResponse, (), {}, b'\x08\x27\x0f'),
        (diag_msg.DiagnosticStatusSimpleResponse, (), {"data": 0x1010}, b'\x08\x27\x0f\x10\x10'),
        (diag_msg.ReturnQueryDataResponse, (), {"message": b'AB'}, b'\x08\x00\x00\x41\x42'),
        (diag_msg.RestartCommunicationsOptionResponse, (), {"toggle": True}, b'\x08\x00\x01\xff\x00'),
        (diag_msg.ReturnDiagnosticRegisterResponse, (), {"data": 0x1010}, b'\x08\x00\x02\x10\x10'),
        (diag_msg.ChangeAsciiInputDelimiterResponse, (), {"data": 0x1010}, b'\x08\x00\x03\x10\x10'),
        (diag_msg.ForceListenOnlyModeResponse, (), {}, b'\x08\x00\x04'),
        (diag_msg.ClearCountersResponse, (), {"data": 0x1010}, b'\x08\x00\n\x10\x10'),
        (diag_msg.ReturnBusMessageCountResponse, (), {"data": 0x1010}, b'\x08\x00\x0b\x10\x10'),
        (diag_msg.ReturnBusCommunicationErrorCountResponse, (), {"data": 0x1010}, b'\x08\x00\x0c\x10\x10'),
        (diag_msg.ReturnBusExceptionErrorCountResponse, (), {"data": 0x1010}, b'\x08\x00\x0d\x10\x10'),
        (diag_msg.ReturnSlaveMessageCountResponse, (), {"data": 0x1010}, b'\x08\x00\x0e\x10\x10'),
        (diag_msg.ReturnSlaveNoResponseCountResponse, (), {"data": 0x1010}, b'\x08\x00\x0f\x10\x10'),
        (diag_msg.ReturnSlaveNAKCountResponse, (), {"data": 0x1010}, b'\x08\x00\x10\x10\x10'),
        (diag_msg.ReturnSlaveBusyCountResponse, (), {"data": 0x1010}, b'\x08\x00\x11\x10\x10'),
        (diag_msg.ReturnSlaveBusCharacterOverrunCountResponse, (), {"data": 0x1010}, b'\x08\x00\x12\x10\x10'),
        (diag_msg.ReturnIopOverrunCountResponse, (), {"data": 0x1010}, b'\x08\x00\x13\x10\x10'),
        (diag_msg.ClearOverrunCountResponse, (), {"data": 0x1010}, b'\x08\x00\x14\x10\x10'),
        (diag_msg.GetClearModbusPlusResponse, (), {"data": 0x1010}, b'\x08\x00\x15\x10\x10'),
        (file_msg.ReadFileRecordResponse, (), {"records": [file_msg.FileRecord(), file_msg.FileRecord()]}, b'\x14\x04\x01\x06\x01\x06'),
        (file_msg.WriteFileRecordResponse, (), {"records": [file_msg.FileRecord(), file_msg.FileRecord()]}, b'\x15\x0e\x06\x00\x00\x00\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00'),
        (file_msg.ReadFifoQueueResponse, (), {"values": [123, 456]}, b'\x18\x00\x06\x00\x04\x00{\x01\xc8'),
        (mei_msg.ReadDeviceInformationResponse, (), {"read_code": 0x17}, b'\x2b\x0e\x17\x83\x00\x00\x00'),
        (o_msg.ReadExceptionStatusResponse, (), {"status": 0x23}, b'\x07\x23'),
        (o_msg.GetCommEventCounterResponse, (), {"count": 123}, b'\x0b\x00\x00\x00\x7b'),
        (o_msg.GetCommEventLogResponse, (), {"status": True, "message_count": 12, "event_count": 7, "events": [12, 14]}, b'\x0c\x08\x00\x00\x00\x07\x00\x0c\x0c\x0e'),
        (o_msg.ReportSlaveIdResponse, (), {"identifier": b'\x12', "status": True}, b'\x11\x02\x12\xff'),
        (reg_r_msg.ReadHoldingRegistersResponse, (), {"values": [3, 17]}, b'\x03\x04\x00\x03\x00\x11'),
        (reg_r_msg.ReadInputRegistersResponse, (), {"values": [3, 17]}, b'\x04\x04\x00\x03\x00\x11'),
        (reg_r_msg.ReadWriteMultipleRegistersResponse, (), {"values": [1, 2]}, b'\x17\x04\x00\x01\x00\x02'),
        (reg_w_msg.WriteSingleRegisterResponse, (), {"address": 117, "value": 112}, b'\x06\x00\x75\x00\x70'),
        (reg_w_msg.WriteMultipleRegistersResponse, (), {"address": 117, "count": 3}, b'\x10\x00\x75\x00\x03'),
        (reg_w_msg.MaskWriteRegisterResponse, (), {"address": 0x0104, "and_mask": 0xE1D2, "or_mask": 0x1234}, b'\x16\x01\x04\xe1\xd2\x12\x34'),
    ]

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests)
    @pytest.mark.usefixtures("kwargs", "args", "frame")
    def test_pdu_instance(self, pdutype):
        """Test that all PDU types can be created."""
        pdu = pdutype()
        assert pdu
        assert str(pdu)

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests + responses)
    @pytest.mark.usefixtures("frame")
    def test_pdu_instance_args(self, pdutype, args, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args, **kwargs)
        assert pdu
        assert str(pdu)

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests + responses)
    @pytest.mark.usefixtures("frame")
    def test_pdu_instance_extras(self, pdutype, args, kwargs):
        """Test that all PDU types can be created."""
        tid = 9112
        slave_id = 63
        pdu = pdutype(*args, transaction=tid, slave=slave_id, **kwargs)
        assert pdu
        assert str(pdu)
        assert pdu.slave_id == slave_id
        assert pdu.transaction_id == tid
        assert pdu.function_code > 0

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests + responses)
    def test_pdu_instance_encode(self, pdutype, args, kwargs, frame):
        """Test that all PDU types can be created."""
        res_frame = pdutype.function_code.to_bytes(1,'big') + pdutype(*args, **kwargs).encode()
        assert res_frame == frame

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), responses)
    @pytest.mark.usefixtures("frame")
    def test_pdu_get_response_pdu_size1(self, pdutype, args, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args, **kwargs)
        assert not pdu.get_response_pdu_size()

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests)
    @pytest.mark.usefixtures("frame")
    def test_get_response_pdu_size2(self, pdutype, args, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args, **kwargs)
        pdu.get_response_pdu_size()
        #FIX size > 0 !!

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests + responses)
    def test_pdu_decode(self, pdutype, args, kwargs, frame):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args, **kwargs)
        pdu.decode(frame[1:])

    @pytest.mark.parametrize(("pdutype", "args", "kwargs", "frame"), requests)
    @pytest.mark.usefixtures("frame")
    async def test_pdu_datastore(self, pdutype, args, kwargs):
        """Test that all PDU types can be created."""
        pdu = pdutype(*args, **kwargs)
        context = MockContext()
        context.validate = lambda a, b, c: True
        assert await pdu.update_datastore(context)


