"""Bit Message Test Fixture."""
from unittest import mock

import pytest

import pymodbus.pdu.bit_message as bit_msg
from pymodbus.constants import ExcCodes


class TestModbusBitMessage:
    """Modbus bit read message tests."""

    def test_bit_read_base_response_encoding(self):
        """Test basic bit message encoding/decoding."""
        for i in range(1, 20):
            data = [True] * i
            pdu = bit_msg.ReadCoilsResponse(bits=data)
            pdu.decode(pdu.encode())
            assert pdu.bits == data

    def test_bit_read_base_requests(self):
        """Test bit read request encoding."""
        for pdu, expected in (
            (bit_msg.ReadCoilsRequest(address=12, count=14), b"\x00\x0c\x00\x0e"),
            (bit_msg.ReadCoilsResponse(bits=[True, False, True, True, False]), b"\x01\x0d"),
        ):
            assert pdu.encode() == expected

    async def test_bit_read_update_datastore_value_errors(self, mock_context):
        """Test bit read request encoding."""
        context = mock_context()
        for pdu in (
            (bit_msg.ReadCoilsRequest(address=1, count=0x800)),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=0x800)),
        ):
            await pdu.update_datastore(context)

    async def test_bit_datastore_exceptions(self, mock_context):
        """Test bit exception response from datastore."""
        context = mock_context()
        context.async_getValues = mock.AsyncMock(return_value=ExcCodes.ILLEGAL_VALUE)
        for pdu in (
            (bit_msg.ReadCoilsRequest(address=1, count=0x800)),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=0x800)),
            (bit_msg.WriteSingleCoilRequest(address=1, bits=[True])),
            (bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True] * 5)),
        ):
            await pdu.update_datastore(context)

    async def test_bit_read_update_datastore_address_errors(self, mock_context):
        """Test bit read request encoding."""
        context = mock_context()
        for pdu in (
            (bit_msg.ReadCoilsRequest(address=1, count=0x800)),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=0x800)),
        ):
            await pdu.update_datastore(context)

    def test_bit_read_get_response_pdu(self):
        """Test bit read message get response pdu."""
        for pdu, expected in (
            (bit_msg.ReadCoilsRequest(address=1, count=5), 3),
            (bit_msg.ReadCoilsRequest(address=1, count=8), 3),
            (bit_msg.ReadCoilsRequest(address=1, count=16), 4),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=21), 5),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=24), 5),
            (bit_msg.ReadDiscreteInputsRequest(address=1, count=1900), 240),
        ):
            assert pdu.get_response_pdu_size() == expected

    def test_bit_write_base_requests(self):
        """Test bit write base."""
        for pdu, expected in (
            (bit_msg.WriteSingleCoilRequest(address=1, bits=[True]), b"\x00\x01\xff\x00"),
            (bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True] * 5), b"\x00\x01\x00\x05\x01\x1f"),
            (bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True]), b"\x00\x01\x00\x01\x01\x01"),
            (bit_msg.WriteMultipleCoilsResponse(address=1, count=5), b"\x00\x01\x00\x05"),
            (bit_msg.WriteMultipleCoilsResponse(address=1, count=1), b"\x00\x01\x00\x01"),
        ):
            assert pdu.encode() == expected

    def test_write_message_get_response_pdu(self):
        """Test bit write message."""
        pdu = bit_msg.WriteSingleCoilRequest(address=1, bits=[True])
        assert pdu.get_response_pdu_size()  == 5

    def test_write_multiple_coils_request(self):
        """Test write multiple coils."""
        for request, frame, values, expected in (
            (bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True] * 5), b"\x00\x01\x00\x05\x01\x1f", [True] * 5, 5),
            (bit_msg.WriteMultipleCoilsRequest(address=1, bits=[True]), b"\x00\x01\x00\x01\x01\x01", [True], 5),
        ):
            request.decode(frame)
            assert request.address == 1
            assert request.bits == values
            assert request.get_response_pdu_size() == expected

    def test_invalid_write_multiple_coils_request(self):
        """Test write invalid multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest(address=1, bits=None)
        assert not request.bits

    def test_write_single_coil_request_encode(self):
        """Test write single coil."""
        request = bit_msg.WriteSingleCoilRequest(address=1, bits=[False])
        assert request.encode() == b"\x00\x01\x00\x00"

    async def test_write_single_coil_update_datastore(self, mock_context):
        """Test write single coil."""
        context = mock_context(False, default=True)
        request = bit_msg.WriteSingleCoilRequest(address=2, bits=[True])
        result = await request.update_datastore(context)

        context.valid = True
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\xff\x00"

        context = mock_context(True, default=False)
        request = bit_msg.WriteSingleCoilRequest(address=2, bits=[False])
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\x00\x00"

    async def test_write_multiple_coils_update_datastore(self, mock_context):
        """Test write multiple coils."""
        context = mock_context(False)
        # too many values
        request = bit_msg.WriteMultipleCoilsRequest(address=2, bits=[])
        result = await request.update_datastore(context)

        # does not verify
        context.valid = False
        request = bit_msg.WriteMultipleCoilsRequest(address=2, bits=[False] * 4)
        result = await request.update_datastore(context)

        # verified request
        context.valid = True
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\x00\x04"

    @pytest.mark.parametrize(("request_pdu"),
        [
            bit_msg.WriteSingleCoilRequest(address=2, bits=[True]),
            bit_msg.WriteMultipleCoilsRequest(address=2, bits=[]),
        ]
    )
    async def test_write_coil_exception(self, request_pdu, mock_context):
        """Test write single coil."""
        context = mock_context(True, default=True)
        context.async_setValues = mock.AsyncMock(return_value=1)
        result = await request_pdu.update_datastore(context)
        assert result.exception_code == 1

    def test_write_multiple_coils_response(self):
        """Test write multiple coils."""
        response = bit_msg.WriteMultipleCoilsResponse()
        response.decode(b"\x00\x80\x00\x08")
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
