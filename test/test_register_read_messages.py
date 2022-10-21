"""Test register read messages."""
import unittest
from test.conftest import FakeList, MockContext

from pymodbus.pdu import ModbusExceptions
from pymodbus.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
    ReadInputRegistersRequest,
    ReadInputRegistersResponse,
    ReadRegistersRequestBase,
    ReadRegistersResponseBase,
    ReadWriteMultipleRegistersRequest,
    ReadWriteMultipleRegistersResponse,
)


TEST_MESSAGE = b"\x06\x00\x0a\x00\x0b\x00\x0c"

# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class ReadRegisterMessagesTest(unittest.TestCase):
    """Register Message Test Fixture.

    This fixture tests the functionality of all the
    register based request/response messages:

    * Read/Write Input Registers
    * Read Holding Registers
    """

    def setUp(self):
        """Initialize the test environment and builds request/result encoding pairs."""
        arguments = {
            "read_address": 1,
            "read_count": 5,
            "write_address": 1,
            "write_registers": [0x00] * 5,
        }
        self.value = 0xABCD
        self.values = [0xA, 0xB, 0xC]
        self.request_read = {
            ReadRegistersRequestBase(1, 5): b"\x00\x01\x00\x05",
            ReadHoldingRegistersRequest(1, 5): b"\x00\x01\x00\x05",
            ReadInputRegistersRequest(1, 5): b"\x00\x01\x00\x05",
            ReadWriteMultipleRegistersRequest(
                **arguments
            ): b"\x00\x01\x00\x05\x00\x01\x00"
            b"\x05\x0a\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00",
        }
        self.response_read = {
            ReadRegistersResponseBase(self.values): TEST_MESSAGE,
            ReadHoldingRegistersResponse(self.values): TEST_MESSAGE,
            ReadInputRegistersResponse(self.values): TEST_MESSAGE,
            ReadWriteMultipleRegistersResponse(self.values): TEST_MESSAGE,
        }

    def tearDown(self):
        """Clean up the test environment."""
        del self.request_read
        del self.response_read

    def test_read_register_response_base(self):
        """Test read register response."""
        response = ReadRegistersResponseBase(list(range(10)))
        for index in range(10):
            self.assertEqual(response.getRegister(index), index)

    def test_register_read_requests(self):
        """Test register read requests."""
        for request, response in iter(self.request_read.items()):
            self.assertEqual(request.encode(), response)

    def test_register_read_responses(self):
        """Test register read response."""
        for request, response in iter(self.response_read.items()):
            self.assertEqual(request.encode(), response)

    def test_register_read_response_decode(self):
        """Test register read response."""
        registers = [
            [0x0A, 0x0B, 0x0C],
            [0x0A, 0x0B, 0x0C],
            [0x0A, 0x0B, 0x0C],
            [0x0A, 0x0B, 0x0C, 0x0A, 0x0B, 0x0C],
        ]
        values = sorted(
            self.response_read.items(),
            key=lambda x: str(x),  # pylint: disable=unnecessary-lambda
        )
        for packet, register in zip(values, registers):
            request, response = packet
            request.decode(response)
            self.assertEqual(request.registers, register)

    def test_register_read_requests_count_errors(self):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        mock = FakeList(0x800)
        requests = [
            ReadHoldingRegistersRequest(1, 0x800),
            ReadInputRegistersRequest(1, 0x800),
            ReadWriteMultipleRegistersRequest(
                read_address=1, read_count=0x800, write_address=1, write_registers=5
            ),
            ReadWriteMultipleRegistersRequest(
                read_address=1, read_count=5, write_address=1, write_registers=mock
            ),
        ]
        for request in requests:
            result = request.execute(None)
            self.assertEqual(ModbusExceptions.IllegalValue, result.exception_code)

    def test_register_read_requests_validate_errors(self):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        context = MockContext()
        requests = [
            ReadHoldingRegistersRequest(-1, 5),
            ReadInputRegistersRequest(-1, 5),
            # ReadWriteMultipleRegistersRequest(-1,5,1,5),
            # ReadWriteMultipleRegistersRequest(1,5,-1,5),
        ]
        for request in requests:
            result = request.execute(context)
            self.assertEqual(ModbusExceptions.IllegalAddress, result.exception_code)

    def test_register_read_requests_execute(self):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        context = MockContext(True)
        requests = [
            ReadHoldingRegistersRequest(-1, 5),
            ReadInputRegistersRequest(-1, 5),
        ]
        for request in requests:
            response = request.execute(context)
            self.assertEqual(request.function_code, response.function_code)

    def test_read_write_multiple_registers_request(self):
        """Test read/write multiple registers."""
        context = MockContext(True)
        request = ReadWriteMultipleRegistersRequest(
            read_address=1, read_count=10, write_address=1, write_registers=[0x00]
        )
        response = request.execute(context)
        self.assertEqual(request.function_code, response.function_code)

    def test_read_write_multiple_registers_validate(self):
        """Test read/write multiple registers."""
        context = MockContext()
        context.validate = lambda f, a, c: a == 1
        request = ReadWriteMultipleRegistersRequest(
            read_address=1, read_count=10, write_address=2, write_registers=[0x00]
        )
        response = request.execute(context)
        self.assertEqual(response.exception_code, ModbusExceptions.IllegalAddress)

        context.validate = lambda f, a, c: a == 2
        response = request.execute(context)
        self.assertEqual(response.exception_code, ModbusExceptions.IllegalAddress)

        request.write_byte_count = 0x100
        response = request.execute(context)
        self.assertEqual(response.exception_code, ModbusExceptions.IllegalValue)

    def test_read_write_multiple_registers_request_decode(self):
        """Test read/write multiple registers."""
        request, response = next(
            (k, v)
            for k, v in self.request_read.items()
            if getattr(k, "function_code", 0) == 23
        )
        request.decode(response)
        self.assertEqual(request.read_address, 0x01)
        self.assertEqual(request.write_address, 0x01)
        self.assertEqual(request.read_count, 0x05)
        self.assertEqual(request.write_count, 0x05)
        self.assertEqual(request.write_byte_count, 0x0A)
        self.assertEqual(request.write_registers, [0x00] * 5)

    def test_serializing_to_string(self):
        """Test serializing to string."""
        for request in iter(self.request_read.keys()):
            self.assertTrue(str(request) is not None)
        for request in iter(self.response_read.keys()):
            self.assertTrue(str(request) is not None)
