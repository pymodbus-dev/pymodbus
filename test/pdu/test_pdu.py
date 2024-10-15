"""Test pdu."""
import pytest

from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import (
    ExceptionResponse,
    IllegalFunctionRequest,
    ModbusExceptions,
    ModbusPDU,
    ModbusResponse,
)


class TestPdu:
    """Unittest for the pymod.pdu module."""

    illegal = IllegalFunctionRequest(1, 0, 0, False)
    exception = ExceptionResponse(1, 1, 0, 0, False)

    async def test_error_methods(self):
        """Test all error methods."""
        self.illegal.decode("12345")
        await self.illegal.execute(None)

        result = self.exception.encode()
        self.exception.decode(result)
        assert result == b"\x01"
        assert self.exception.exception_code == 1

    def test_request_exception_factory(self):
        """Test all error methods."""
        request = ModbusPDU(0, 0, False)
        request.function_code = 1
        errors = {ModbusExceptions.decode(c): c for c in range(1, 20)}
        for error, code in iter(errors.items()):
            result = request.doException(code)
            assert str(result) == f"Exception Response(129, 1, {error})"

    def test_calculate_rtu_frame_size(self):
        """Test the calculation of Modbus/RTU frame sizes."""
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
        ModbusPDU._rtu_byte_count_pos = None  # pylint: disable=protected-access

        with pytest.raises(NotImplementedException):
            ModbusResponse.calculateRtuFrameSize(b"")
        ModbusResponse._rtu_frame_size = 12  # pylint: disable=protected-access
        assert ModbusResponse.calculateRtuFrameSize(b"") == 12
        ModbusResponse._rtu_frame_size = None  # pylint: disable=protected-access
        ModbusResponse._rtu_byte_count_pos = 2  # pylint: disable=protected-access
        assert (
            ModbusResponse.calculateRtuFrameSize(
                b"\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"
            )
            == 0x05 + 5
        )
        ModbusResponse._rtu_byte_count_pos = None  # pylint: disable=protected-access
