"""Test pdu."""
import pytest

from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import (
    ExceptionResponse,
    ModbusExceptions,
    ModbusPDU,
)


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
        request.setData(0, 0, False)
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
