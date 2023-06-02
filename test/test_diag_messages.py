"""Test diag messages."""
import pytest

from pymodbus.constants import ModbusPlusOperation
from pymodbus.diag_message import (
    ChangeAsciiInputDelimiterRequest,
    ChangeAsciiInputDelimiterResponse,
    ClearCountersRequest,
    ClearCountersResponse,
    ClearOverrunCountRequest,
    ClearOverrunCountResponse,
    DiagnosticStatusRequest,
    DiagnosticStatusResponse,
    DiagnosticStatusSimpleRequest,
    DiagnosticStatusSimpleResponse,
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
    ReturnSlaveNoResponseCountRequest,
    ReturnSlaveNoResponseCountResponse,
)
from pymodbus.exceptions import NotImplementedException


class TestDataStore:
    """Unittest for the pymodbus.diag_message module."""

    requests = [
        (
            RestartCommunicationsOptionRequest,
            b"\x00\x01\x00\x00",
            b"\x00\x01\xff\x00",
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
        (ReturnSlaveMessageCountRequest, b"\x00\x0e\x00\x00", b"\x00\x0e\x00\x00"),
        (
            ReturnSlaveNoResponseCountRequest,
            b"\x00\x0f\x00\x00",
            b"\x00\x0f\x00\x00",
        ),
        (ReturnSlaveNAKCountRequest, b"\x00\x10\x00\x00", b"\x00\x10\x00\x00"),
        (ReturnSlaveBusyCountRequest, b"\x00\x11\x00\x00", b"\x00\x11\x00\x00"),
        (
            ReturnSlaveBusCharacterOverrunCountRequest,
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
        # (DiagnosticStatusResponse,                     b"\x00\x00\x00\x00"),
        # (DiagnosticStatusSimpleResponse,               b"\x00\x00\x00\x00"),
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
        (ReturnSlaveMessageCountResponse, b"\x00\x0e\x00\x00"),
        (ReturnSlaveNoResponseCountResponse, b"\x00\x0f\x00\x00"),
        (ReturnSlaveNAKCountResponse, b"\x00\x10\x00\x00"),
        (ReturnSlaveBusyCountResponse, b"\x00\x11\x00\x00"),
        (ReturnSlaveBusCharacterOverrunCountResponse, b"\x00\x12\x00\x00"),
        (ReturnIopOverrunCountResponse, b"\x00\x13\x00\x00"),
        (ClearOverrunCountResponse, b"\x00\x14\x00\x00"),
        (GetClearModbusPlusResponse, b"\x00\x15\x00\x04" + b"\x00\x00" * 55),
    ]

    def test_diagnostic_encode_decode(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        for msg in (DiagnosticStatusRequest, DiagnosticStatusResponse):
            msg_obj = msg()
            data = b"\x00\x01\x02\x03"
            msg_obj.decode(data)
            result = msg_obj.encode()
            assert data == result

    def test_diagnostic_requests_decode(self):
        """Testing diagnostic request messages encoding"""
        for msg, enc, _ in self.requests:
            handle = DiagnosticStatusRequest()
            handle.decode(enc)
            assert handle.sub_function_code == msg.sub_function_code
            encoded = handle.encode()
            assert enc == encoded

    def test_diagnostic_simple_requests(self):
        """Testing diagnostic request messages encoding"""
        request = DiagnosticStatusSimpleRequest(b"\x12\x34")
        request.sub_function_code = 0x1234
        with pytest.raises(NotImplementedException):
            request.execute()
        assert request.encode() == b"\x12\x34\x12\x34"
        DiagnosticStatusSimpleResponse(None)

    def test_diagnostic_response_decode(self):
        """Testing diagnostic request messages encoding"""
        for msg, enc, _ in self.requests:
            handle = DiagnosticStatusResponse()
            handle.decode(enc)
            assert handle.sub_function_code == msg.sub_function_code

    def test_diagnostic_requests_encode(self):
        """Testing diagnostic request messages encoding"""
        for msg, enc, _ in self.requests:
            assert msg().encode() == enc

    def test_diagnostic_execute(self):
        """Testing diagnostic message execution"""
        for message, encoded, executed in self.requests:
            encoded = message().execute().encode()
            assert encoded == executed

    def test_return_query_data_request(self):
        """Testing diagnostic message execution"""
        message = ReturnQueryDataRequest([0x0000] * 2)
        assert message.encode() == b"\x00\x00\x00\x00\x00\x00"
        message = ReturnQueryDataRequest(0x0000)
        assert message.encode() == b"\x00\x00\x00\x00"

    def test_return_query_data_response(self):
        """Testing diagnostic message execution"""
        message = ReturnQueryDataResponse([0x0000] * 2)
        assert message.encode() == b"\x00\x00\x00\x00\x00\x00"
        message = ReturnQueryDataResponse(0x0000)
        assert message.encode() == b"\x00\x00\x00\x00"

    def test_restart_cmmunications_option(self):
        """Testing diagnostic message execution"""
        request = RestartCommunicationsOptionRequest(True)
        assert request.encode() == b"\x00\x01\xff\x00"
        request = RestartCommunicationsOptionRequest(False)
        assert request.encode() == b"\x00\x01\x00\x00"

        response = RestartCommunicationsOptionResponse(True)
        assert response.encode() == b"\x00\x01\xff\x00"
        response = RestartCommunicationsOptionResponse(False)
        assert response.encode() == b"\x00\x01\x00\x00"

    def test_get_clear_modbus_plus_request_execute(self):
        """Testing diagnostic message execution"""
        request = GetClearModbusPlusRequest(data=ModbusPlusOperation.ClearStatistics)
        response = request.execute()
        assert response.message == ModbusPlusOperation.ClearStatistics

        request = GetClearModbusPlusRequest(data=ModbusPlusOperation.GetStatistics)
        response = request.execute()
        resp = [ModbusPlusOperation.GetStatistics]
        assert response.message == resp + [0x00] * 55
