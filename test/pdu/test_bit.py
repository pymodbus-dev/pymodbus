"""Bit Message Test Fixture."""

from unittest import mock

import pytest

import pymodbus.pdu.bit_message as bit_msg
from pymodbus.constants import ExcCodes
from pymodbus.pdu.decoders import DecodePDU


class TestModbusBitMessage:
    """Modbus bit read message tests."""

    def test_bit_read_base_response_encoding(self):
        """Test basic bit message encoding/decoding."""
        for i in range(1, 20):
            data = [True] * i
            expected = data + [False] * (-len(data) % 8)
            pdu = bit_msg.ReadCoilsResponse(bits=data)
            pdu.x_decode(pdu.x_encode())
            assert pdu.bits == expected

    def test_bit_read_base_requests(self):
        """Test bit read request encoding."""
        for pdu, expected in (
            (bit_msg.ReadCoilsRequest(address=12, count=14), b"\x00\x0c\x00\x0e"),
            (
                bit_msg.ReadCoilsResponse(bits=[True, False, True, True, False]),
                b"\x01\x0d",
            ),
        ):
            assert pdu.x_encode() == expected

    async def test_bit_read_datastore_update_value_errors(self, mock_server_context):
        """Test bit read request encoding."""
        context = mock_server_context()
        for pdu in (
            (bit_msg.ReadCoilsRequest(address=1, count=0x800)),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=0x800)),
        ):
            await pdu.datastore_update(context, 1)

    @pytest.mark.parametrize(
        ("request_class", "function_code"),
        [
            (bit_msg.ReadCoilsRequest, 1),
            (bit_msg.ReadDiscreteInputsRequest, 2),
        ],
    )
    async def test_bit_read_count_above_max_returns_illegal_value(
        self, request_class, function_code, mock_server_context
    ):
        """An out-of-range bit read quantity must answer 0x03, not silence."""
        context = mock_server_context()
        context.async_getValues = mock.AsyncMock(return_value=[True] * 10)
        request = request_class(address=0, count=request_class.MAX_COUNT + 1)
        result = await request.datastore_update(context, 1)
        assert result.function_code == function_code | 0x80
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE
        context.async_getValues.assert_not_awaited()

    @pytest.mark.parametrize(
        "request_class",
        [bit_msg.ReadCoilsRequest, bit_msg.ReadDiscreteInputsRequest],
    )
    async def test_bit_read_count_zero_returns_illegal_value(
        self, request_class, mock_server_context
    ):
        """A zero bit read quantity must answer 0x03."""
        context = mock_server_context()
        context.async_getValues = mock.AsyncMock(return_value=[True] * 10)
        result = await request_class(address=0, count=0).datastore_update(context, 1)
        assert result.function_code == request_class.function_code | 0x80
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE
        context.async_getValues.assert_not_awaited()

    @pytest.mark.parametrize(
        "request_class",
        [bit_msg.ReadCoilsRequest, bit_msg.ReadDiscreteInputsRequest],
    )
    async def test_bit_read_count_at_max_returns_normal_response(
        self, request_class, mock_server_context
    ):
        """A count exactly at the maximum must be accepted, not rejected."""
        context = mock_server_context()
        request = request_class(address=0, count=request_class.MAX_COUNT)
        result = await request.datastore_update(context, 1)
        assert result.function_code == request_class.function_code

    def test_bit_read_decode_accepts_count_above_max(self):
        """Decoding must not raise for an over-max bit read quantity."""
        decoder = DecodePDU(True)
        for frame, expected_count in (
            (b"\x01\x00\x00\x07\xd1", 2001),
            (b"\x02\x00\x00\x07\xd1", 2001),
        ):
            pdu = decoder.decode(frame)
            assert pdu.count == expected_count

    async def test_bit_datastore_exceptions(self, mock_server_context):
        """Test bit exception response from datastore."""
        context = mock_server_context()
        context.async_getValues = mock.AsyncMock(return_value=ExcCodes.ILLEGAL_VALUE)
        for pdu in (
            (bit_msg.ReadCoilsRequest(address=1, count=5)),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=5)),
            (bit_msg.WriteSingleCoilRequest(address=1, bits=[True])),
            (bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True] * 5)),
        ):
            await pdu.datastore_update(context, 0)

    async def test_bit_read_datastore_update_address_errors(self, mock_server_context):
        """Test bit read request encoding."""
        context = mock_server_context()
        for pdu in (
            (bit_msg.ReadCoilsRequest(address=1, count=0x800)),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=0x800)),
        ):
            await pdu.datastore_update(context, 1)

    def test_bit_write_base_requests(self):
        """Test bit write base."""
        for pdu, expected in (
            (
                bit_msg.WriteSingleCoilRequest(address=1, bits=[True]),
                b"\x00\x01\xff\x00",
            ),
            (
                bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True] * 5),
                b"\x00\x01\x00\x05\x01\x1f",
            ),
            (
                bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True]),
                b"\x00\x01\x00\x01\x01\x01",
            ),
            (
                bit_msg.WriteMultipleCoilsResponse(address=1, count=5),
                b"\x00\x01\x00\x05",
            ),
            (
                bit_msg.WriteMultipleCoilsResponse(address=1, count=1),
                b"\x00\x01\x00\x01",
            ),
        ):
            assert pdu.x_encode() == expected

    def test_write_message_coil(self):
        """Test bit write message."""
        _ = bit_msg.WriteSingleCoilRequest(address=1, bits=[True])

    def test_write_multiple_coils_request(self):
        """Test write multiple coils."""
        for request, frame, values in (
            (
                bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True] * 5),
                b"\x00\x01\x00\x05\x01\x1f",
                [True] * 5,
            ),
            (
                bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True]),
                b"\x00\x01\x00\x01\x01\x01",
                [True],
            ),
        ):
            request.x_decode(frame)
            assert request.address == 1
            assert request.bits == values

    def test_invalid_write_multiple_coils_request(self):
        """Test write invalid multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest(address=1, bits=None)
        assert not request.bits

    @pytest.mark.parametrize(
        "frame",
        [
            b"\x00\x01\x00\x10\x01\xff",
            b"\x00\x01\x00\x08\x02\xff\x00",
            b"\x00\x01\x00\x08\x01",
            b"\x00\x01\x00\x08\x01\xff\x00",
        ],
    )
    async def test_write_multiple_coils_rejects_invalid_byte_count(
        self, frame, mock_server_context
    ):
        """Test write multiple coils rejects inconsistent byte counts."""
        request = bit_msg.WriteMultipleCoilsRequest()
        request.x_decode(frame)
        context = mock_server_context()
        context.async_setValues = mock.AsyncMock()

        result = await request.datastore_update(context, 0)

        assert result.exception_code == ExcCodes.ILLEGAL_VALUE
        context.async_setValues.assert_not_awaited()

    async def test_write_multiple_coils_accepts_valid_byte_count(
        self, mock_server_context
    ):
        """Test write multiple coils accepts a consistent byte count."""
        request = bit_msg.WriteMultipleCoilsRequest()
        request.x_decode(b"\x00\x01\x00\x09\x02\xff\x01")
        context = mock_server_context()
        context.async_setValues = mock.AsyncMock(return_value=0)

        result = await request.datastore_update(context, 0)

        assert result.count == 9
        context.async_setValues.assert_awaited_once_with(
            0, request.function_code, 1, [True] * 9
        )

    def test_write_single_coil_request_encode(self):
        """Test write single coil."""
        request = bit_msg.WriteSingleCoilRequest(address=1, bits=[False])
        assert request.x_encode() == b"\x00\x01\x00\x00"

    async def test_write_single_coil_datastore_update(self, mock_server_context):
        """Test write single coil."""
        context = mock_server_context(False, default=True)
        request = bit_msg.WriteSingleCoilRequest(address=2, bits=[True])
        result = await request.datastore_update(context, 1)

        context.valid = True
        result = await request.datastore_update(context, 0)
        assert result.x_encode() == b"\x00\x02\xff\x00"

        context = mock_server_context(True, default=False)
        request = bit_msg.WriteSingleCoilRequest(address=2, bits=[False])
        result = await request.datastore_update(context, 0)
        assert result.x_encode() == b"\x00\x02\x00\x00"

    async def test_write_multiple_coils_datastore_update(self, mock_server_context):
        """Test write multiple coils."""
        context = mock_server_context(False)
        # too many values
        request = bit_msg.WriteMultipleCoilsRequest(address=2, bits=[])
        result = await request.datastore_update(context, 0)

        # does not verify
        context.valid = False
        request = bit_msg.WriteMultipleCoilsRequest(address=2, bits=[False] * 4)
        result = await request.datastore_update(context, 0)

        # verified request
        context.valid = True
        result = await request.datastore_update(context, 0)
        assert result.x_encode() == b"\x00\x02\x00\x04"

    @pytest.mark.parametrize(
        ("request_pdu"),
        [
            bit_msg.WriteSingleCoilRequest(address=2, bits=[True]),
            bit_msg.WriteMultipleCoilsRequest(address=2, bits=[]),
        ],
    )
    async def test_write_coil_exception(self, request_pdu, mock_server_context):
        """Test write single coil."""
        context = mock_server_context(True, default=True)
        context.async_setValues = mock.AsyncMock(return_value=1)
        result = await request_pdu.datastore_update(context, 1)
        assert result.exception_code == 1

    def test_write_multiple_coils_response(self):
        """Test write multiple coils."""
        response = bit_msg.WriteMultipleCoilsResponse()
        response.x_decode(b"\x00\x80\x00\x08")
        assert response.address == 0x80
        assert response.count == 0x08

    def test_serializing_to_string(self):
        """Test serializing to string."""
        for pdu in (
            bit_msg.WriteSingleCoilRequest(address=1, bits=[True]),
            bit_msg.WriteSingleCoilResponse(address=1, bits=[True]),
            bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True] * 5),
            bit_msg.WriteMultipleCoilsResponse(address=1, count=5),
        ):
            assert str(pdu)

    def test_pass_falsy_value_in_write_multiple_coils_request(self):
        """Test pass falsy value to write multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest(address=1, bits=[False])
        assert request.bits == [False]
