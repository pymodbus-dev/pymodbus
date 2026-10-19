"""Test register read messages."""

import struct
from unittest import mock

import pytest

from pymodbus.constants import ExcCodes
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu.decoders import DecodePDU
from pymodbus.pdu.register_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
    ReadInputRegistersRequest,
    ReadInputRegistersResponse,
    ReadWriteMultipleRegistersRequest,
    ReadWriteMultipleRegistersResponse,
)


TEST_MESSAGE = b"\x06\x00\x0a\x00\x0b\x00\x0c"


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
            ): b"\x00\x01\x00\x05\x00\x01\x00\x01\x02\x00\xab",
        }
        self.response_read = {
            ReadHoldingRegistersResponse(registers=self.values): TEST_MESSAGE,
            ReadInputRegistersResponse(registers=self.values): TEST_MESSAGE,
            ReadWriteMultipleRegistersResponse(registers=self.values): TEST_MESSAGE,
        }

    def test_register_read_requests(self):
        """Test register read requests."""
        for request, response in iter(self.request_read.items()):
            assert request.x_encode() == response

    def test_register_read_responses(self):
        """Test register read response."""
        for request, response in iter(self.response_read.items()):
            assert request.x_encode() == response

    def test_register_read_response_decode(self):
        """Test register read response."""
        for response, packet in self.response_read.items():
            response.x_decode(packet)
            assert response.registers == self.values

    def test_register_read_response_decode_error(self):
        """Test register read response."""
        reg = ReadHoldingRegistersResponse(count=5)
        with pytest.raises(ModbusIOException) as exc_info:
            reg.x_decode(b"\x14\x00\x03\x00\x11")
        assert exc_info.value.fcode == reg.function_code + 0x80

    def test_register_input_response_decode_error(self):
        """Test register read response."""
        reg = ReadInputRegistersResponse(count=5)
        with pytest.raises(ModbusIOException) as exc_info:
            reg.x_decode(b"\x14\x00\x03\x00\x11")
        assert exc_info.value.fcode == reg.function_code + 0x80

    def test_readwrite_response_decode_error(self):
        """Test register read response."""
        reg = ReadWriteMultipleRegistersResponse(count=5)
        with pytest.raises(ModbusIOException) as exc_info:
            reg.x_decode(b"\x14\x00\x03\x00\x11")
        assert exc_info.value.fcode == reg.function_code + 0x80

    def test_readwrite_encode_write_count_limit(self):
        """Encoding must reject a write count above the FC23 maximum of 121.

        121 write registers is a 252 byte PDU, 122 is 254 and does not fit in
        the 253 byte MODBUS PDU.
        """

        def build(count):
            return ReadWriteMultipleRegistersRequest(
                read_address=1,
                read_count=1,
                write_address=1,
                write_registers=[0] * count,
            )

        assert len(build(121).x_encode()) + 1 <= 253
        with pytest.raises(ValueError):  # noqa: PT011
            build(122).x_encode()

    def test_readwrite_decode_write_count_above_limit(self):
        """Decoding must accept 122..125 so the server can answer ILLEGAL_VALUE.

        Raising here would make the server drop the frame without a response.
        """
        request = ReadWriteMultipleRegistersRequest()
        request.x_decode(struct.pack(">HHHHB", 1, 1, 1, 122, 244) + b"\x00\x00" * 122)
        assert request.write_count == 122

    def test_readwrite_decode_read_count_above_limit(self):
        """Decoding must accept read_count above 125 so the server can answer 0x03."""
        request = ReadWriteMultipleRegistersRequest()
        request.x_decode(struct.pack(">HHHHB", 1, 126, 1, 1, 2) + b"\x00\x00")
        assert request.read_count == 126

    async def test_readwrite_read_count_above_limit_returns_illegal_value(
        self, mock_server_context
    ):
        """An out-of-range FC23 read count must answer 0x03."""
        context = mock_server_context()
        request = ReadWriteMultipleRegistersRequest(
            read_address=1, read_count=126, write_address=1, write_registers=[5]
        )
        result = await request.datastore_update(context, 1)
        assert result.function_code == 0x97
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

    async def test_register_read_requests_count_errors(self, mock_server_context):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        context = mock_server_context()
        requests = [
            ReadHoldingRegistersRequest(address=1, count=0x800),
            ReadInputRegistersRequest(address=1, count=0x800),
            ReadWriteMultipleRegistersRequest(
                read_address=1, read_count=0x800, write_address=1, write_registers=[5]
            ),
            ReadWriteMultipleRegistersRequest(
                read_address=1, read_count=5, write_address=1, write_registers=[]
            ),
        ]
        for request in requests:
            result = await request.datastore_update(context, 0)
            assert result.exception_code == ExcCodes.ILLEGAL_VALUE

    @pytest.mark.parametrize(
        ("request_class", "function_code"),
        [
            (ReadHoldingRegistersRequest, 3),
            (ReadInputRegistersRequest, 4),
        ],
    )
    async def test_read_register_count_above_max_returns_illegal_value(
        self, request_class, function_code, mock_server_context
    ):
        """An out-of-range read quantity must answer 0x03, not silence."""
        context = mock_server_context()
        context.async_getValues = mock.AsyncMock(return_value=[1] * 10)
        request = request_class(address=0, count=request_class.MAX_COUNT + 1)
        result = await request.datastore_update(context, 1)
        assert result.function_code == function_code | 0x80
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE
        context.async_getValues.assert_not_awaited()

    @pytest.mark.parametrize(
        "request_class",
        [ReadHoldingRegistersRequest, ReadInputRegistersRequest],
    )
    async def test_read_register_count_zero_returns_illegal_value(
        self, request_class, mock_server_context
    ):
        """A zero read quantity must answer 0x03."""
        context = mock_server_context()
        result = await request_class(address=0, count=0).datastore_update(context, 1)
        assert result.function_code == request_class.function_code | 0x80
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

    def test_read_register_decode_accepts_count_above_max(self):
        """Decoding must not raise for an over-max read quantity.

        Raising here makes DecodePDU.decode() swallow the frame and the server
        answer nothing, replacing a correct exception response with silence.
        """
        decoder = DecodePDU(True)
        for frame, expected_count in (
            (b"\x03\x00\x00\x00\x7e", 126),
            (b"\x04\x00\x00\x00\x7e", 126),
        ):
            pdu = decoder.decode(frame)
            assert pdu.count == expected_count

    async def test_register_read_requests_verify_errors(self, mock_server_context):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        context = mock_server_context()
        requests = [
            ReadHoldingRegistersRequest(address=-1, count=5),
            ReadInputRegistersRequest(address=-1, count=5),
            ReadWriteMultipleRegistersRequest(-1, 5, 1, [5]),
            ReadWriteMultipleRegistersRequest(1, 5, -1, [5]),
        ]
        for request in requests:
            await request.datastore_update(context, 0)

    async def test_register_read_requests_datastore_update(self, mock_server_context):
        """This tests that the register request messages.

        will break on counts that are out of range
        """
        context = mock_server_context(True)
        requests = [
            ReadHoldingRegistersRequest(address=-1, count=5),
            ReadInputRegistersRequest(address=-1, count=5),
        ]
        for request in requests:
            response = await request.datastore_update(context, 1)
            assert request.function_code == response.function_code

    async def test_read_write_multiple_registers_request(self, mock_server_context):
        """Test read/write multiple registers."""
        context = mock_server_context(True)
        request = ReadWriteMultipleRegistersRequest(
            read_address=1, read_count=10, write_address=1, write_registers=[0x00]
        )
        response = await request.datastore_update(context, 0)
        assert request.function_code == response.function_code

    @pytest.mark.parametrize(
        "frame",
        [
            b"\x00\x01\x00\x01\x00\x02\x00\x02\x02\x00\x0a",
            b"\x00\x01\x00\x01\x00\x02\x00\x01\x04\x00\x0a\x00\x0b",
            b"\x00\x01\x00\x01\x00\x02\x00\x01\x02\x00",
            b"\x00\x01\x00\x01\x00\x02\x00\x01\x02\x00\x0a\x00",
            b"\x00\x01\x00\x01\x00\x02\x00\x01\x01\x00",
        ],
    )
    async def test_read_write_multiple_registers_rejects_invalid_byte_count(
        self, frame, mock_server_context
    ):
        """Test inconsistent write byte counts are rejected before writing."""
        request = ReadWriteMultipleRegistersRequest()
        request.x_decode(frame)
        context = mock_server_context()
        context.async_setValues = mock.AsyncMock()

        result = await request.datastore_update(context, 1)

        assert result.exception_code == ExcCodes.ILLEGAL_VALUE
        context.async_setValues.assert_not_awaited()

    async def test_read_write_multiple_registers_accepts_valid_byte_count(
        self, mock_server_context
    ):
        """Test a consistent write byte count reaches the datastore."""
        request = ReadWriteMultipleRegistersRequest()
        request.x_decode(b"\x00\x01\x00\x01\x00\x02\x00\x02\x04\x00\x0a\x00\x0b")
        context = mock_server_context()
        context.async_setValues = mock.AsyncMock(return_value=0)

        result = await request.datastore_update(context, 1)

        assert result.function_code == request.function_code
        context.async_setValues.assert_awaited_once_with(
            1, request.function_code, 2, [0x0A, 0x0B]
        )

    async def test_read_write_multiple_registers_verify(self, mock_server_context):
        """Test read/write multiple registers."""
        context = mock_server_context()
        request = ReadWriteMultipleRegistersRequest(
            read_address=1, read_count=0x200, write_address=2, write_registers=[0x00]
        )
        response = await request.datastore_update(context, 0)
        assert response.exception_code == ExcCodes.ILLEGAL_VALUE

        await request.datastore_update(context, 0)
        assert response.exception_code == ExcCodes.ILLEGAL_VALUE

        request.write_byte_count = 0x100
        await request.datastore_update(context, 0)
        assert response.exception_code == ExcCodes.ILLEGAL_VALUE

    async def test_register_datastore_exceptions(self, mock_server_context):
        """Test exception response from datastore."""
        context = mock_server_context()
        context.async_getValues = mock.AsyncMock(return_value=ExcCodes.ILLEGAL_VALUE)
        for pdu in (
            ReadHoldingRegistersRequest(address=-1, count=5),
            ReadInputRegistersRequest(address=-1, count=5),
            ReadWriteMultipleRegistersRequest(-1, 5, 1, [5], 1),
        ):
            await pdu.datastore_update(context, 1)

    def test_serializing_to_string(self):
        """Test serializing to string."""
        for request in iter(self.request_read.keys()):
            assert str(request)
        for request in iter(self.response_read.keys()):
            assert str(request)

    @pytest.mark.parametrize(
        ("request_pdu"),
        [
            ReadWriteMultipleRegistersRequest(
                read_address=1, read_count=5, write_address=1, write_registers=[5]
            ),
        ],
    )
    async def test_register_read_exception(self, request_pdu, mock_server_context):
        """Test write single coil."""
        context = mock_server_context(True, default=True)
        context.async_setValues = mock.AsyncMock(return_value=1)
        result = await request_pdu.datastore_update(context, 1)
        assert result.exception_code == 1
