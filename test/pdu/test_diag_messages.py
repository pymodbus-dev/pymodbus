"""Test diag messages."""
import pytest

from pymodbus.constants import ModbusPlusOperation, ModbusStatus
from pymodbus.pdu.diag_message import (
    ChangeAsciiInputDelimiterRequest,
    ChangeAsciiInputDelimiterResponse,
    ClearCountersRequest,
    ClearCountersResponse,
    ClearOverrunCountRequest,
    ClearOverrunCountResponse,
    DiagnosticBase,
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
    ReturnDeviceBusCharacterOverrunCountRequest,
    ReturnDeviceBusCharacterOverrunCountResponse,
    ReturnDeviceBusyCountRequest,
    ReturnDeviceBusyCountResponse,
    ReturnDeviceMessageCountRequest,
    ReturnDeviceMessageCountResponse,
    ReturnDeviceNAKCountRequest,
    ReturnDeviceNAKCountResponse,
    ReturnDeviceNoResponseCountRequest,
    ReturnDeviceNoResponseCountResponse,
    ReturnDiagnosticRegisterRequest,
    ReturnDiagnosticRegisterResponse,
    ReturnIopOverrunCountRequest,
    ReturnIopOverrunCountResponse,
    ReturnQueryDataRequest,
    ReturnQueryDataResponse,
)


class TestDataStore:
    """Unittest for the pymodbus.diag_message module."""

    requests = [
        (
            RestartCommunicationsOptionRequest,
            b"\x00\x01\x00\x00",
            b"\x00\x01\x00\x00",
        ),
        (ReturnDiagnosticRegisterRequest, b"\x00\x02\x00\x00", b"\x00\x02\x00\x00"),
        (
            ChangeAsciiInputDelimiterRequest,
            b"\x00\x03\x00\x00",
            b"\x00\x03\x00\x00",
        ),
        (ForceListenOnlyModeRequest, b"\x00\x04\x00\x00", b"\x00\x04"),
        (ReturnQueryDataRequest, b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"),
        (ClearCountersRequest, b"\x00\x0a\x00\x00", b"\x00\x0a\x00\x00"),
        (ReturnBusMessageCountRequest, b"\x00\x0b\x00\x00", b"\x00\x0b\x00\x00"),
        (
            ReturnBusCommunicationErrorCountRequest,
            b"\x00\x0c\x00\x00",
            b"\x00\x0c\x00\x00",
        ),
        (
            ReturnBusExceptionErrorCountRequest,
            b"\x00\x0d\x00\x00",
            b"\x00\x0d\x00\x00",
        ),
        (ReturnDeviceMessageCountRequest, b"\x00\x0e\x00\x00", b"\x00\x0e\x00\x00"),
        (
            ReturnDeviceNoResponseCountRequest,
            b"\x00\x0f\x00\x00",
            b"\x00\x0f\x00\x00",
        ),
        (ReturnDeviceNAKCountRequest, b"\x00\x10\x00\x00", b"\x00\x10\x00\x00"),
        (ReturnDeviceBusyCountRequest, b"\x00\x11\x00\x00", b"\x00\x11\x00\x00"),
        (
            ReturnDeviceBusCharacterOverrunCountRequest,
            b"\x00\x12\x00\x00",
            b"\x00\x12\x00\x00",
        ),
        (ReturnIopOverrunCountRequest, b"\x00\x13\x00\x00", b"\x00\x13\x00\x00"),
        (ClearOverrunCountRequest, b"\x00\x14\x00\x00", b"\x00\x14\x00\x00"),
        (
            GetClearModbusPlusRequest,
            b"\x00\x15\x00\x00",
            b"\x00\x15\x00\x00" + b"\x00\x00" * 55,
        ),
    ]

    responses = [
        (DiagnosticBase,                     b"\x00\x00\x00\x00"),
        (DiagnosticBase,               b"\x00\x00\x00\x00"),
        (ReturnQueryDataResponse, b"\x00\x00\x00\x00"),
        (RestartCommunicationsOptionResponse, b"\x00\x01\x00\x00"),
        (ReturnDiagnosticRegisterResponse, b"\x00\x02\x00\x00"),
        (ChangeAsciiInputDelimiterResponse, b"\x00\x03\x00\x00"),
        (ForceListenOnlyModeResponse, b"\x00\x04"),
        (ReturnQueryDataResponse, b"\x00\x00\x00\x00"),
        (ClearCountersResponse, b"\x00\x0a\x00\x00"),
        (ReturnBusMessageCountResponse, b"\x00\x0b\x00\x00"),
        (ReturnBusCommunicationErrorCountResponse, b"\x00\x0c\x00\x00"),
        (ReturnBusExceptionErrorCountResponse, b"\x00\x0d\x00\x00"),
        (ReturnDeviceMessageCountResponse, b"\x00\x0e\x00\x00"),
        (ReturnDeviceNoResponseCountResponse, b"\x00\x0f\x00\x00"),
        (ReturnDeviceNAKCountResponse, b"\x00\x10\x00\x00"),
        (ReturnDeviceBusyCountResponse, b"\x00\x11\x00\x00"),
        (ReturnDeviceBusCharacterOverrunCountResponse, b"\x00\x12\x00\x00"),
        (ReturnIopOverrunCountResponse, b"\x00\x13\x00\x00"),
        (ClearOverrunCountResponse, b"\x00\x14\x00\x00"),
        (GetClearModbusPlusResponse, b"\x00\x15\x00\x04" + b"\x00\x00" * 55),
    ]

    def test_diagnostic_encode_decode(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        msg_obj = DiagnosticBase()
        data = b"\x00\x01\x02\x03"
        msg_obj.decode(data)
        result = msg_obj.encode()
        assert data == result

    def test_diagnostic_encode_error(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        msg_obj = DiagnosticBase()
        msg_obj.message = "not allowed"
        with pytest.raises(TypeError):
            msg_obj.encode()

    def test_diagnostic_decode_error(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        msg_obj = DiagnosticBase()
        data = b"\x00\x01\x02\x03a"
        msg_obj.decode(data)

    def test_diagnostic_requests_decode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            handle = DiagnosticBase()
            handle.decode(enc)
            assert handle.sub_function_code == msg.sub_function_code
            encoded = handle.encode()
            assert enc == encoded

    async def test_diagnostic_simple_requests(self):
        """Testing diagnostic request messages encoding."""
        request = DiagnosticBase(message=b"\x12\x34")
        request.sub_function_code = 0x1234
        assert request.encode() == b"\x12\x34\x12\x34"
        DiagnosticBase()

    def test_diagnostic_response_decode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            handle = DiagnosticBase()
            handle.decode(enc)
            assert handle.sub_function_code == msg.sub_function_code

    def test_diagnostic_requests_encode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            assert msg().encode() == enc

    async def test_diagnostic_update_datastore(self):
        """Testing diagnostic message execution."""
        for message, encoded, update_datastored in self.requests:
            encoded = (await message().update_datastore(None)).encode()
            assert encoded == update_datastored

    def test_return_query_data_request(self):
        """Testing diagnostic message execution."""
        message = ReturnQueryDataRequest(b"\x00\x00\x00\x00")
        assert message.encode() == b"\x00\x00\x00\x00\x00\x00"
        message = ReturnQueryDataRequest(b"\x00\x00")
        assert message.encode() == b"\x00\x00\x00\x00"

    def test_return_query_data_response(self):
        """Testing diagnostic message execution."""
        message = ReturnQueryDataResponse(b"\x00\x00\x00\x00")
        assert message.encode() == b"\x00\x00\x00\x00\x00\x00"
        message = ReturnQueryDataResponse(b"\x00\x00")
        assert message.encode() == b"\x00\x00\x00\x00"

    def test_restart_communications_option(self):
        """Testing diagnostic message execution."""
        request = RestartCommunicationsOptionRequest(message=ModbusStatus.ON)
        assert request.encode() == b"\x00\x01\xff\x00"
        request = RestartCommunicationsOptionRequest(message=ModbusStatus.OFF)
        assert request.encode() == b"\x00\x01\x00\x00"

        response = RestartCommunicationsOptionResponse(message=ModbusStatus.ON)
        assert response.encode() == b"\x00\x01\xff\x00"
        response = RestartCommunicationsOptionResponse(message=ModbusStatus.OFF)
        assert response.encode() == b"\x00\x01\x00\x00"

    async def test_get_clear_modbus_plus_request_update_datastore(self):
        """Testing diagnostic message execution."""
        request = GetClearModbusPlusRequest(message=ModbusPlusOperation.CLEAR_STATISTICS)
        response = await request.update_datastore(None)
        assert response.message == ModbusPlusOperation.CLEAR_STATISTICS

        request = GetClearModbusPlusRequest(message=ModbusPlusOperation.GET_STATISTICS)
        response = await request.update_datastore(None)
        resp = [ModbusPlusOperation.GET_STATISTICS]
        assert response.message == resp + [0x00] * 55
