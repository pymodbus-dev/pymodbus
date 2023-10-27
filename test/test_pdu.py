"""Test pdu."""
import pytest

from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import (
    ExceptionResponse,
    IllegalFunctionRequest,
    ModbusExceptions,
    ModbusRequest,
    ModbusResponse,
)


class TestPdu:
    """Unittest for the pymod.pdu module."""

    bad_requests = (
        ModbusRequest(),
        ModbusResponse(),
    )
    illegal = IllegalFunctionRequest(1)
    exception = ExceptionResponse(1, 1)

    def test_not_impelmented(self):
        """Test a base classes for not implemented functions."""
        for request in self.bad_requests:
            with pytest.raises(NotImplementedException):
                request.encode()

        for request in self.bad_requests:
            with pytest.raises(NotImplementedException):
                request.decode(None)

    def test_error_methods(self):
        """Test all error methods."""
        self.illegal.decode("12345")
        self.illegal.execute(None)

        result = self.exception.encode()
        self.exception.decode(result)
        assert result == b"\x01"
        assert self.exception.exception_code == 1

    def test_request_exception_factory(self):
        """Test all error methods."""
        request = ModbusRequest()
        request.function_code = 1
        errors = {ModbusExceptions.decode(c): c for c in range(1, 20)}
        for error, code in iter(errors.items()):
            result = request.doException(code)
            assert str(result) == f"Exception Response(129, 1, {error})"

    def test_calculate_rtu_frame_size(self):
        """Test the calculation of Modbus/RTU frame sizes."""
        with pytest.raises(NotImplementedException):
            ModbusRequest.calculateRtuFrameSize(b"")
        ModbusRequest._rtu_frame_size = 5  # pylint: disable=protected-access
        assert ModbusRequest.calculateRtuFrameSize(b"") == 5
        del ModbusRequest._rtu_frame_size

        ModbusRequest._rtu_byte_count_pos = 2  # pylint: disable=protected-access
        assert (
            ModbusRequest.calculateRtuFrameSize(
                b"\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"
            )
            == 0x05 + 5
        )
        del ModbusRequest._rtu_byte_count_pos

        with pytest.raises(NotImplementedException):
            ModbusResponse.calculateRtuFrameSize(b"")
        ModbusResponse._rtu_frame_size = 12  # pylint: disable=protected-access
        assert ModbusResponse.calculateRtuFrameSize(b"") == 12
        del ModbusResponse._rtu_frame_size
        ModbusResponse._rtu_byte_count_pos = 2  # pylint: disable=protected-access
        assert (
            ModbusResponse.calculateRtuFrameSize(
                b"\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"
            )
            == 0x05 + 5
        )
        del ModbusResponse._rtu_byte_count_pos
