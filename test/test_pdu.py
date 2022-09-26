"""Test pdu."""
import unittest

from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import (
    ExceptionResponse,
    IllegalFunctionRequest,
    ModbusExceptions,
    ModbusRequest,
    ModbusResponse,
)


class SimplePduTest(unittest.TestCase):
    """Unittest for the pymod.pdu module."""

    def setUp(self):
        """Initialize the test environment"""
        self.bad_requests = (
            ModbusRequest(),
            ModbusResponse(),
        )
        self.illegal = IllegalFunctionRequest(1)
        self.exception = ExceptionResponse(1, 1)

    def tearDown(self):
        """Clean up the test environment"""
        del self.bad_requests
        del self.illegal
        del self.exception

    def test_not_impelmented(self):
        """Test a base classes for not implemented functions"""
        for request in self.bad_requests:
            self.assertRaises(NotImplementedException, request.encode)

        for request in self.bad_requests:
            self.assertRaises(NotImplementedException, request.decode, None)

    def test_error_methods(self):
        """Test all error methods"""
        self.illegal.decode("12345")
        self.illegal.execute(None)

        result = self.exception.encode()
        self.exception.decode(result)
        self.assertEqual(result, b"\x01")
        self.assertEqual(self.exception.exception_code, 1)

    def test_request_exception_factory(self):
        """Test all error methods"""
        request = ModbusRequest()
        request.function_code = 1
        errors = {ModbusExceptions.decode(c): c for c in range(1, 20)}
        for error, code in iter(errors.items()):
            result = request.doException(code)
            self.assertEqual(str(result), f"Exception Response(129, 1, {error})")

    def test_calculate_rtu_frame_size(self):
        """Test the calculation of Modbus/RTU frame sizes"""
        self.assertRaises(
            NotImplementedException, ModbusRequest.calculateRtuFrameSize, b""
        )
        ModbusRequest._rtu_frame_size = 5  # pylint: disable=protected-access
        self.assertEqual(ModbusRequest.calculateRtuFrameSize(b""), 5)
        del ModbusRequest._rtu_frame_size

        ModbusRequest._rtu_byte_count_pos = 2  # pylint: disable=protected-access
        self.assertEqual(
            ModbusRequest.calculateRtuFrameSize(
                b"\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"
            ),
            0x05 + 5,
        )
        del ModbusRequest._rtu_byte_count_pos

        self.assertRaises(
            NotImplementedException, ModbusResponse.calculateRtuFrameSize, b""
        )
        ModbusResponse._rtu_frame_size = 12  # pylint: disable=protected-access
        self.assertEqual(ModbusResponse.calculateRtuFrameSize(b""), 12)
        del ModbusResponse._rtu_frame_size
        ModbusResponse._rtu_byte_count_pos = 2  # pylint: disable=protected-access
        self.assertEqual(
            ModbusResponse.calculateRtuFrameSize(
                b"\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"
            ),
            0x05 + 5,
        )
        del ModbusResponse._rtu_byte_count_pos
