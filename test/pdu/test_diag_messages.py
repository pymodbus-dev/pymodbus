"""Test diag messages."""

from typing import cast
from unittest import mock

import pytest

import pymodbus.pdu.diag_message as pdu_diag
from pymodbus.constants import CLEAR_STATISTICS, GET_STATISTICS, ModbusStatus
from pymodbus.pdu import ModbusControlBlock


class TestDataStore:
    """Unittest for the pymodbus.diag_message module."""

    requests = [
        (
            pdu_diag.PDUrestartCommunicationsOption,
            b"\x00\x01\x00\x00",
            b"\x00\x01\x00\x00",
        ),
        (
            pdu_diag.PDUreturnDiagnosticRegister,
            b"\x00\x02\x00\x00",
            b"\x00\x02\x00\x00",
        ),
        (
            pdu_diag.PDUchangeAsciiInputDelimiter,
            b"\x00\x03\x00\x00",
            b"\x00\x03\x00\x00",
        ),
        (pdu_diag.PDUforceListenOnlyMode, b"\x00\x04\x00\x00", b"\x00\x04"),
        (pdu_diag.PDUreturnQueryData, b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"),
        (pdu_diag.PDUclearCounters, b"\x00\x0a\x00\x00", b"\x00\x0a\x00\x00"),
        (pdu_diag.PDUreturnBusMessageCount, b"\x00\x0b\x00\x00", b"\x00\x0b\x00\x00"),
        (
            pdu_diag.PDUreturnBusCommunicationErrorCount,
            b"\x00\x0c\x00\x00",
            b"\x00\x0c\x00\x00",
        ),
        (
            pdu_diag.PDUreturnBusExceptionErrorCount,
            b"\x00\x0d\x00\x00",
            b"\x00\x0d\x00\x00",
        ),
        (
            pdu_diag.PDUreturnDeviceMessageCount,
            b"\x00\x0e\x00\x00",
            b"\x00\x0e\x00\x00",
        ),
        (
            pdu_diag.PDUreturnDeviceNoResponseCount,
            b"\x00\x0f\x00\x00",
            b"\x00\x0f\x00\x00",
        ),
        (pdu_diag.PDUreturnDeviceNAKCount, b"\x00\x10\x00\x00", b"\x00\x10\x00\x00"),
        (pdu_diag.PDUreturnDeviceBusyCount, b"\x00\x11\x00\x00", b"\x00\x11\x00\x00"),
        (
            pdu_diag.PDUreturnDeviceBusCharacterOverrunCount,
            b"\x00\x12\x00\x00",
            b"\x00\x12\x00\x00",
        ),
        (pdu_diag.PDUreturnIopOverrunCount, b"\x00\x13\x00\x00", b"\x00\x13\x00\x00"),
        (pdu_diag.PDUclearOverrunCount, b"\x00\x14\x00\x00", b"\x00\x14\x00\x00"),
        (
            pdu_diag.PDUgetClearModbusPlus,
            b"\x00\x15\x00\x00",
            b"\x00\x15\x00\x00" + b"\x00\x00" * 55,
        ),
    ]

    responses = [
        (pdu_diag.PDUdiagnostic, b"\x00\x00\x00\x00"),
        (pdu_diag.PDUdiagnostic, b"\x00\x00\x00\x00"),
        (pdu_diag.PDUreturnQueryData, b"\x00\x00\x00\x00"),
        (pdu_diag.PDUrestartCommunicationsOption, b"\x00\x01\x00\x00"),
        (pdu_diag.PDUreturnDiagnosticRegister, b"\x00\x02\x00\x00"),
        (pdu_diag.PDUchangeAsciiInputDelimiter, b"\x00\x03\x00\x00"),
        (pdu_diag.PDUforceListenOnlyMode, b"\x00\x04"),
        (pdu_diag.PDUreturnQueryData, b"\x00\x00\x00\x00"),
        (pdu_diag.PDUclearCounters, b"\x00\x0a\x00\x00"),
        (pdu_diag.PDUreturnBusMessageCount, b"\x00\x0b\x00\x00"),
        (pdu_diag.PDUreturnBusCommunicationErrorCount, b"\x00\x0c\x00\x00"),
        (pdu_diag.PDUreturnBusExceptionErrorCount, b"\x00\x0d\x00\x00"),
        (pdu_diag.PDUreturnDeviceMessageCount, b"\x00\x0e\x00\x00"),
        (pdu_diag.PDUreturnDeviceNoResponseCount, b"\x00\x0f\x00\x00"),
        (pdu_diag.PDUreturnDeviceNAKCount, b"\x00\x10\x00\x00"),
        (pdu_diag.PDUreturnDeviceBusyCount, b"\x00\x11\x00\x00"),
        (pdu_diag.PDUreturnDeviceBusCharacterOverrunCount, b"\x00\x12\x00\x00"),
        (pdu_diag.PDUreturnIopOverrunCount, b"\x00\x13\x00\x00"),
        (pdu_diag.PDUclearOverrunCount, b"\x00\x14\x00\x00"),
        (pdu_diag.PDUgetClearModbusPlus, b"\x00\x15\x00\x04" + b"\x00\x00" * 55),
    ]

    def test_diagnostic_encode_decode(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        msg_obj = pdu_diag.PDUdiagnostic()
        data = b"\x00\x01\x02\x03"
        msg_obj.from_bytes(0, data)
        result = msg_obj.to_bytes()
        assert data == result

    def test_diagnostic_encode_error(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        msg_obj = pdu_diag.PDUdiagnostic()
        msg_obj.message = "not allowed"  # type: ignore[assignment]
        with pytest.raises(TypeError):
            msg_obj.to_bytes()

    def test_diagnostic_decode_error(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        msg_obj = pdu_diag.PDUdiagnostic()
        data = b"\x00\x01\x02\x03a"
        msg_obj.from_bytes(0, data)

    def test_diagnostic_requests_decode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            handle = pdu_diag.PDUdiagnostic()
            handle.from_bytes(0, enc)
            assert handle.sub_function_code == msg.sub_function_code
            encoded = handle.to_bytes()
            assert enc == encoded

    async def test_diagnostic_simple_requests(self):
        """Testing diagnostic request messages encoding."""
        request = pdu_diag.PDUdiagnostic(message=b"\x12\x34")
        request.sub_function_code = 0x1234
        assert request.to_bytes() == b"\x12\x34\x12\x34"
        pdu_diag.PDUdiagnostic()

    def test_diagnostic_response_decode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            handle = pdu_diag.PDUdiagnostic()
            handle.from_bytes(0, enc)
            assert handle.sub_function_code == msg.sub_function_code

    def test_diagnostic_requests_encode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            assert msg().to_bytes() == enc

    async def test_diagnostic_build_response(self):
        """Testing diagnostic message execution."""
        control = ModbusControlBlock()
        try:
            for message, encoded, result in self.requests:
                encoded = (
                    await message().build_response(mock.AsyncMock(), mock.AsyncMock())
                ).to_bytes()
                assert encoded == result
        finally:
            control.Delimiter = b"\n"

    def test_return_query_data_request(self):
        """Testing diagnostic message execution."""
        message = pdu_diag.PDUreturnQueryData(b"\x00\x00\x00\x00")
        assert message.to_bytes() == b"\x00\x00\x00\x00\x00\x00"
        message = pdu_diag.PDUreturnQueryData(b"\x00\x00")
        assert message.to_bytes() == b"\x00\x00\x00\x00"

    def test_return_query_data_response(self):
        """Testing diagnostic message execution."""
        message = pdu_diag.PDUreturnQueryData(b"\x00\x00\x00\x00")
        assert message.to_bytes() == b"\x00\x00\x00\x00\x00\x00"
        message = pdu_diag.PDUreturnQueryData(b"\x00\x00")
        assert message.to_bytes() == b"\x00\x00\x00\x00"

    def test_restart_communications_option(self):
        """Testing diagnostic message execution."""
        request = pdu_diag.PDUrestartCommunicationsOption(message=ModbusStatus.ON)
        assert request.to_bytes() == b"\x00\x01\xff\x00"
        request = pdu_diag.PDUrestartCommunicationsOption(message=ModbusStatus.OFF)
        assert request.to_bytes() == b"\x00\x01\x00\x00"

        response = pdu_diag.PDUrestartCommunicationsOption(message=ModbusStatus.ON)
        assert response.to_bytes() == b"\x00\x01\xff\x00"
        response = pdu_diag.PDUrestartCommunicationsOption(message=ModbusStatus.OFF)
        assert response.to_bytes() == b"\x00\x01\x00\x00"

    async def test_get_clear_modbus_plus_request_build_responsee(self):
        """Testing diagnostic message execution."""
        request = pdu_diag.PDUgetClearModbusPlus(message=CLEAR_STATISTICS)
        response = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert (
            cast(pdu_diag.PDUgetClearModbusPlus, response).message == CLEAR_STATISTICS
        )

        request = pdu_diag.PDUgetClearModbusPlus(message=GET_STATISTICS)
        response = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert (
            cast(pdu_diag.PDUgetClearModbusPlus, response).message
            == GET_STATISTICS + b"\x00" * 55
        )
