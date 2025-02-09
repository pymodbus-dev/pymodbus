"""Test register read messages."""
import pytest

from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import ExceptionResponse
from pymodbus.pdu.register_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
    ReadInputRegistersRequest,
    ReadInputRegistersResponse,
    ReadWriteMultipleRegistersRequest,
    ReadWriteMultipleRegistersResponse,
)


TEST_MESSAGE = b"\x06\x00\x0a\x00\x0b\x00\x0c"

# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class TestReadRegisterMessages:
    """Register Message Test Fixture.

    This fixture tests the functionality of all the
    register based request/response messages:

    * Read/Write Input Registers
    * Read Holding Registers
    """

    values: list
    request_read: dict
    response_read: dict

    def setup_method(self):
        """Initialize the test environment and builds request/result encoding pairs."""
        arguments = {
            "read_address": 1,
            "read_count": 5,
            "write_address": 1,
        }
        self.values = [0xA, 0xB, 0xC]
        self.request_read = {
            ReadHoldingRegistersRequest(address=1, count=5): b"\x00\x01\x00\x05",
            ReadInputRegistersRequest(address=1, count=5): b"\x00\x01\x00\x05",
            ReadWriteMultipleRegistersRequest(
                write_registers=[0x00] * 5,
                **arguments,
            ): b"\x00\x01\x00\x05\x00\x01\x00"
            b"\x05\x0a\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00",
            ReadWriteMultipleRegistersRequest(
                write_registers=[0xAB],
                **arguments,
            ): b"\x00\x01\x00\x05\x00\x01\x00" b"\x01\x02\x00\xAB",
        }
        self.response_read = {
            ReadHoldingRegistersResponse(registers=self.values): TEST_MESSAGE,
            ReadInputRegistersResponse(registers=self.values): TEST_MESSAGE,
            ReadWriteMultipleRegistersResponse(registers=self.values): TEST_MESSAGE,
        }

    def test_register_read_requests(self):
        """Test register read requests."""
        for request, response in iter(self.request_read.items()):
            assert request.encode() == response

    def test_register_read_responses(self):
        """Test register read response."""
        for request, response in iter(self.response_read.items()):
            assert request.encode() == response

    def test_register_read_response_decode(self):
        """Test register read response."""
        for response, packet in self.response_read.items():
            response.decode(packet)
            assert response.registers == self.values

    def test_register_read_response_decode_error(self):
        """Test register read response."""
        reg = ReadHoldingRegistersResponse(count = 5)
        with pytest.raises(ModbusIOException):
            reg.decode(b'\x14\x00\x03\x00\x11')

    async def test_register_read_requests_count_errors(self):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        requests = [
            #ReadHoldingRegistersRequest(address=1, count=0x800),
            #ReadInputRegistersRequest(address=1, count=0x800),
            ReadWriteMultipleRegistersRequest(
                read_address=1, read_count=0x800, write_address=1, write_registers=[5]
            ),
            ReadWriteMultipleRegistersRequest(
                read_address=1, read_count=5, write_address=1, write_registers=[]
            ),
        ]
        for request in requests:
            result = await request.update_datastore(None)
            assert result.exception_code == ExceptionResponse.ILLEGAL_VALUE

    async def test_register_read_requests_verify_errors(self, mock_context):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        context = mock_context()
        requests = [
            ReadHoldingRegistersRequest(address=-1, count=5),
            ReadInputRegistersRequest(address=-1, count=5),
            # ReadWriteMultipleRegistersRequest(-1,5,1,5),
            # ReadWriteMultipleRegistersRequest(1,5,-1,5),
        ]
        for request in requests:
            await request.update_datastore(context)

    async def test_register_read_requests_update_datastore(self, mock_context):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        context = mock_context(True)
        requests = [
            ReadHoldingRegistersRequest(address=-1, count=5),
            ReadInputRegistersRequest(address=-1, count=5),
        ]
        for request in requests:
            response = await request.update_datastore(context)
            assert request.function_code == response.function_code

    async def test_read_write_multiple_registers_request(self, mock_context):
        """Test read/write multiple registers."""
        context = mock_context(True)
        request = ReadWriteMultipleRegistersRequest(
            read_address=1, read_count=10, write_address=1, write_registers=[0x00]
        )
        response = await request.update_datastore(context)
        assert request.function_code == response.function_code

    async def test_read_write_multiple_registers_verify(self, mock_context):
        """Test read/write multiple registers."""
        context = mock_context()
        request = ReadWriteMultipleRegistersRequest(
            read_address=1, read_count=10, write_address=2, write_registers=[0x00]
        )
        await request.update_datastore(context)
        #assert response.exception_code == ExceptionResponse.ILLEGAL_ADDRESS

        await request.update_datastore(context)
        #assert response.exception_code == ExceptionResponse.ILLEGAL_ADDRESS

        request.write_byte_count = 0x100
        await request.update_datastore(context)
        #assert response.exception_code == ExceptionResponse.ILLEGAL_VALUE

    def test_serializing_to_string(self):
        """Test serializing to string."""
        for request in iter(self.request_read.keys()):
            assert str(request)
        for request in iter(self.response_read.keys()):
            assert str(request)
