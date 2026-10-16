"""Test diag messages."""

from typing import cast

import pytest

import pymodbus.pdu.diag_message as pdu_diag
from pymodbus.constants import ModbusPlusOperation, ModbusStatus
from pymodbus.datastore import ModbusServerContext
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
        msg_obj.x_decode(data)
        result = msg_obj.x_encode()
        assert data == result

    def test_diagnostic_encode_error(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        msg_obj = pdu_diag.PDUdiagnostic()
        msg_obj.message = "not allowed"  # type: ignore[assignment]
        with pytest.raises(TypeError):
            msg_obj.x_encode()

    def test_diagnostic_decode_error(self):
        """Testing diagnostic request/response can be decoded and encoded."""
        msg_obj = pdu_diag.PDUdiagnostic()
        data = b"\x00\x01\x02\x03a"
        msg_obj.x_decode(data)

    def test_diagnostic_requests_decode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            handle = pdu_diag.PDUdiagnostic()
            handle.x_decode(enc)
            assert handle.sub_function_code == msg.sub_function_code
            encoded = handle.x_encode()
            assert enc == encoded

    async def test_diagnostic_simple_requests(self):
        """Testing diagnostic request messages encoding."""
        request = pdu_diag.PDUdiagnostic(message=b"\x12\x34")
        request.sub_function_code = 0x1234
        assert request.x_encode() == b"\x12\x34\x12\x34"
        pdu_diag.PDUdiagnostic()

    def test_diagnostic_response_decode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            handle = pdu_diag.PDUdiagnostic()
            handle.x_decode(enc)
            assert handle.sub_function_code == msg.sub_function_code

    def test_diagnostic_requests_encode(self):
        """Testing diagnostic request messages encoding."""
        for msg, enc, _ in self.requests:
            assert msg().x_encode() == enc

    async def test_diagnostic_datastore_update(self):
        """Testing diagnostic message execution."""
        control = ModbusControlBlock()
        try:
            for message, encoded, datastore_updated in self.requests:
                encoded = (
                    await message().datastore_update(cast(ModbusServerContext, None), 1)
                ).x_encode()
                assert encoded == datastore_updated
        finally:
            control.Delimiter = b"\n"

    def test_return_query_data_request(self):
        """Testing diagnostic message execution."""
        message = pdu_diag.PDUreturnQueryData(b"\x00\x00\x00\x00")
        assert message.x_encode() == b"\x00\x00\x00\x00\x00\x00"
        message = pdu_diag.PDUreturnQueryData(b"\x00\x00")
        assert message.x_encode() == b"\x00\x00\x00\x00"

    def test_return_query_data_response(self):
        """Testing diagnostic message execution."""
        message = pdu_diag.PDUreturnQueryData(b"\x00\x00\x00\x00")
        assert message.x_encode() == b"\x00\x00\x00\x00\x00\x00"
        message = pdu_diag.PDUreturnQueryData(b"\x00\x00")
        assert message.x_encode() == b"\x00\x00\x00\x00"

    def test_restart_communications_option(self):
        """Testing diagnostic message execution."""
        request = pdu_diag.PDUrestartCommunicationsOption(message=ModbusStatus.ON)
        assert request.x_encode() == b"\x00\x01\xff\x00"
        request = pdu_diag.PDUrestartCommunicationsOption(message=ModbusStatus.OFF)
        assert request.x_encode() == b"\x00\x01\x00\x00"

        response = pdu_diag.PDUrestartCommunicationsOption(message=ModbusStatus.ON)
        assert response.x_encode() == b"\x00\x01\xff\x00"
        response = pdu_diag.PDUrestartCommunicationsOption(message=ModbusStatus.OFF)
        assert response.x_encode() == b"\x00\x01\x00\x00"

    async def test_get_clear_modbus_plus_request_datastore_update(self):
        """Testing diagnostic message execution."""
        request = pdu_diag.PDUgetClearModbusPlus(
            message=ModbusPlusOperation.CLEAR_STATISTICS
        )
        response = await request.datastore_update(cast(ModbusServerContext, None), 0)
        assert (
            cast(pdu_diag.PDUgetClearModbusPlus, response).message
            == ModbusPlusOperation.CLEAR_STATISTICS
        )

        request = pdu_diag.PDUgetClearModbusPlus(
            message=ModbusPlusOperation.GET_STATISTICS
        )
        response = await request.datastore_update(cast(ModbusServerContext, None), 0)
        resp = [ModbusPlusOperation.GET_STATISTICS]
        assert (
            cast(pdu_diag.PDUgetClearModbusPlus, response).message == resp + [0x00] * 55
        )
