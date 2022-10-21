"""Test register write messages."""
import unittest
from test.conftest import MockContext, MockLastValuesContext

from pymodbus.payload import BinaryPayloadBuilder, Endian
from pymodbus.pdu import ModbusExceptions
from pymodbus.register_write_message import (
    MaskWriteRegisterRequest,
    MaskWriteRegisterResponse,
    WriteMultipleRegistersRequest,
    WriteMultipleRegistersResponse,
    WriteSingleRegisterRequest,
    WriteSingleRegisterResponse,
)


# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class WriteRegisterMessagesTest(unittest.TestCase):
    """Register Message Test Fixture.

    This fixture tests the functionality of all the
    register based request/response messages:

    * Read/Write Input Registers
    * Read Holding Registers
    """

    def setUp(self):
        """Initialize the test environment and builds request/result encoding pairs."""
        self.value = 0xABCD
        self.values = [0xA, 0xB, 0xC]
        builder = BinaryPayloadBuilder(byteorder=Endian.Big)
        builder.add_16bit_uint(0x1234)
        self.payload = builder.build()
        self.write = {
            WriteSingleRegisterRequest(1, self.value): b"\x00\x01\xab\xcd",
            WriteSingleRegisterResponse(1, self.value): b"\x00\x01\xab\xcd",
            WriteMultipleRegistersRequest(
                1, self.values
            ): b"\x00\x01\x00\x03\x06\x00\n\x00\x0b\x00\x0c",
            WriteMultipleRegistersResponse(1, 5): b"\x00\x01\x00\x05",
            WriteSingleRegisterRequest(
                1, self.payload[0], skip_encode=True
            ): b"\x00\x01\x12\x34",
            WriteMultipleRegistersRequest(
                1, self.payload, skip_encode=True
            ): b"\x00\x01\x00\x01\x02\x12\x34",
        }

    def tearDown(self):
        """Clean up the test environment"""
        del self.write

    def test_register_write_requests_encode(self):
        """Test register write requests encode."""
        for request, response in iter(self.write.items()):
            self.assertEqual(request.encode(), response)

    def test_register_write_requests_decode(self):
        """Test register write requests decode."""
        addresses = [1, 1, 1, 1]
        values = sorted(
            self.write.items(),
            key=lambda x: str(x),  # pylint: disable=unnecessary-lambda
        )
        for packet, address in zip(values, addresses):
            request, response = packet
            request.decode(response)
            self.assertEqual(request.address, address)

    def test_invalid_write_multiple_registers_request(self):
        """Test invalid write multiple registers request."""
        request = WriteMultipleRegistersRequest(0, None)
        self.assertEqual(request.values, [])

    def test_serializing_to_string(self):
        """Test serializing to string."""
        for request in iter(self.write.keys()):
            self.assertTrue(str(request) is not None)

    def test_write_single_register_request(self):
        """Test write single register request."""
        context = MockContext()
        request = WriteSingleRegisterRequest(0x00, 0xF0000)
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        request.value = 0x00FF
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalAddress)

        context.valid = True
        result = request.execute(context)
        self.assertEqual(result.function_code, request.function_code)

    def test_write_multiple_register_request(self):
        """Test write multiple register request."""
        context = MockContext()
        request = WriteMultipleRegistersRequest(0x00, [0x00] * 10)
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalAddress)

        request.count = 0x05  # bytecode != code * 2
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        request.count = 0x800  # outside of range
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        context.valid = True
        request = WriteMultipleRegistersRequest(0x00, [0x00] * 10)
        result = request.execute(context)
        self.assertEqual(result.function_code, request.function_code)

        # -----------------------------------------------------------------------#
        # Mask Write Register Request
        # -----------------------------------------------------------------------#

    def test_mask_write_register_request_encode(self):
        """Test basic bit message encoding/decoding"""
        handle = MaskWriteRegisterRequest(0x0000, 0x0101, 0x1010)
        result = handle.encode()
        self.assertEqual(result, b"\x00\x00\x01\x01\x10\x10")

    def test_mask_write_register_request_decode(self):
        """Test basic bit message encoding/decoding"""
        request = b"\x00\x04\x00\xf2\x00\x25"
        handle = MaskWriteRegisterRequest()
        handle.decode(request)
        self.assertEqual(handle.address, 0x0004)
        self.assertEqual(handle.and_mask, 0x00F2)
        self.assertEqual(handle.or_mask, 0x0025)

    def test_mask_write_register_request_execute(self):
        """Test write register request valid execution"""
        # The test uses the 4 nibbles of the 16-bit values to test
        # the combinations:
        #     and_mask=0, or_mask=0
        #     and_mask=F, or_mask=0
        #     and_mask=0, or_mask=F
        #     and_mask=F, or_mask=F
        context = MockLastValuesContext(valid=True, default=0xAA55)
        handle = MaskWriteRegisterRequest(0x0000, 0x0F0F, 0x00FF)
        result = handle.execute(context)
        self.assertTrue(isinstance(result, MaskWriteRegisterResponse))
        self.assertEqual([0x0AF5], context.last_values)

    def test_mask_write_register_request_invalid_execute(self):
        """Test write register request execute with invalid data"""
        context = MockContext(valid=False, default=0x0000)
        handle = MaskWriteRegisterRequest(0x0000, -1, 0x1010)
        result = handle.execute(context)
        self.assertEqual(ModbusExceptions.IllegalValue, result.exception_code)

        handle = MaskWriteRegisterRequest(0x0000, 0x0101, -1)
        result = handle.execute(context)
        self.assertEqual(ModbusExceptions.IllegalValue, result.exception_code)

        handle = MaskWriteRegisterRequest(0x0000, 0x0101, 0x1010)
        result = handle.execute(context)
        self.assertEqual(ModbusExceptions.IllegalAddress, result.exception_code)

        # -----------------------------------------------------------------------#
        # Mask Write Register Response
        # -----------------------------------------------------------------------#

    def test_mask_write_register_response_encode(self):
        """Test basic bit message encoding/decoding"""
        handle = MaskWriteRegisterResponse(0x0000, 0x0101, 0x1010)
        result = handle.encode()
        self.assertEqual(result, b"\x00\x00\x01\x01\x10\x10")

    def test_mask_write_register_response_decode(self):
        """Test basic bit message encoding/decoding"""
        request = b"\x00\x04\x00\xf2\x00\x25"
        handle = MaskWriteRegisterResponse()
        handle.decode(request)
        self.assertEqual(handle.address, 0x0004)
        self.assertEqual(handle.and_mask, 0x00F2)
        self.assertEqual(handle.or_mask, 0x0025)
