"""Bit Message Test Fixture."""

from unittest import mock

import pytest

import pymodbus.pdu.bit_message as bit_msg
from pymodbus.constants import ExcCodes
from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu import DecodePDU


class TestBitMessage:
    """Modbus bit read message tests."""

    def test_bit_1(self):
        """Test basic to_from_bytes."""
        for i in range(1, 20):
            data = [True] * i
            pdu = bit_msg.PDUreadCoils(0, is_request=False, bits=data)
            pdu.from_bytes(0, pdu.to_bytes())
            assert pdu.bits == data + [False] * (-len(data) % 8)

    @pytest.mark.parametrize(
        ("pdu", "msg"),
        [
            (bit_msg.PDUreadCoils(0, address=12, count=14), b"\x00\x0c\x00\x0e"),
            (
                bit_msg.PDUreadCoils(
                    0, is_request=False, bits=[True, False, True, True, False]
                ),
                b"\x01\x0d",
            ),
        ],
    )
    def test_bit_2(self, pdu, msg):
        """Test bit to_bytes."""
        assert pdu.to_bytes() == msg

    @pytest.mark.parametrize(
        "pdu", [bit_msg.PDUreadCoils, bit_msg.PDUreadDiscreteInputs]
    )
    @pytest.mark.parametrize(
        "cases",
        [
            "ok",
            "build",
            "0",
            "max",
        ],
    )
    async def test_bit_3(self, pdu, cases):
        """An out-of-range bit read quantity must answer 0x03, not silence."""
        match cases:
            case "ok":
                pdu(1, address=0, count=pdu.MAX_COUNT)
            case "build":
                x = pdu(1, address=0, count=pdu.MAX_COUNT)
                await x.build_response(
                    mock.AsyncMock(return_value=[True] * 1999),
                    mock.AsyncMock(return_value=0),
                )
            case "0":
                with pytest.raises(ModbusIOException):
                    pdu(0, address=0, count=0)
            case "max":
                with pytest.raises(ModbusIOException):
                    pdu(0, address=0, count=pdu.MAX_COUNT + 1)

    @pytest.mark.parametrize(
        ("frame", "exp_count"),
        [
            (b"\x01\x00\x00\x07\xd1", 2001),
            (b"\x02\x00\x00\x07\xd1", 2001),
        ],
    )
    def test_bit_4(self, frame, exp_count):
        """Decoding must not raise for an over-max bit read quantity."""
        assert DecodePDU(True).decode(frame).count == exp_count

    async def test_bit_datastore_exceptions(self):
        """Test bit exception response from datastore."""
        for pdu in (
            (bit_msg.PDUreadCoils(0, address=1, count=5)),
            (bit_msg.PDUreadDiscreteInputs(0, address=1, count=5)),
            (bit_msg.PDUwriteSingleCoil(0, address=1, bits=[True])),
            (bit_msg.PDUwriteMultipleCoils(0, address=1, bits=[True] * 5)),
        ):
            await pdu.build_response(
                mock.AsyncMock(return_value=ExcCodes.ILLEGAL_VALUE),
                mock.AsyncMock(return_value=0),
            )

    def test_bit_write_base_requests(self):
        """Test bit write base."""
        for pdu, expected in (
            (
                bit_msg.PDUwriteSingleCoil(0, address=1, bits=[True]),
                b"\x00\x01\xff\x00",
            ),
            (
                bit_msg.PDUwriteMultipleCoils(0, address=1, bits=[True] * 5),
                b"\x00\x01\x00\x05\x01\x1f",
            ),
            (
                bit_msg.PDUwriteMultipleCoils(0, address=1, bits=[True]),
                b"\x00\x01\x00\x01\x01\x01",
            ),
            (
                bit_msg.PDUwriteMultipleCoils(0, is_request=False, address=1, count=5),
                b"\x00\x01\x00\x05",
            ),
            (
                bit_msg.PDUwriteMultipleCoils(0, is_request=False, address=1, count=1),
                b"\x00\x01\x00\x01",
            ),
        ):
            assert pdu.to_bytes() == expected

    def test_write_message_coil(self):
        """Test bit write message."""
        _ = bit_msg.PDUwriteSingleCoil(0, address=1, bits=[True])

    def test_write_multiple_coils_request(self):
        """Test write multiple coils."""
        for request, frame, values in (
            (
                bit_msg.PDUwriteMultipleCoils(0, address=1, bits=[True] * 5),
                b"\x00\x01\x00\x05\x01\x1f",
                [True] * 5,
            ),
            (
                bit_msg.PDUwriteMultipleCoils(0, address=1, bits=[True]),
                b"\x00\x01\x00\x01\x01\x01",
                [True],
            ),
        ):
            request.from_bytes(0, frame)
            assert request.address == 1
            assert request.bits == values

    def test_invalid_write_multiple_coils_request(self):
        """Test write invalid multiple coils."""
        request = bit_msg.PDUwriteMultipleCoils(0, address=1, bits=None)
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
    async def test_write_multiple_coils_rejects_invalid_byte_count(self, frame):
        """Test write multiple coils rejects inconsistent byte counts."""
        request = bit_msg.PDUwriteMultipleCoils(0)
        request.from_bytes(0, frame)
        mx = mock.AsyncMock(return_value=ExcCodes.ILLEGAL_VALUE)
        result = await request.build_response(mx, mx)
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

    async def test_write_multiple_coils_accepts_valid_byte_count(
        self,
    ):
        """Test write multiple coils accepts a consistent byte count."""
        request = bit_msg.PDUwriteMultipleCoils(0)
        request.from_bytes(0, b"\x00\x01\x00\x09\x02\xff\x01")
        result = await request.build_response(
            mock.AsyncMock(return_value=[True]), mock.AsyncMock(return_value=0)
        )
        assert result.count == 9

    def test_write_single_coil_request_encode(self):
        """Test write single coil."""
        request = bit_msg.PDUwriteSingleCoil(0, address=1, bits=[False])
        assert request.to_bytes() == b"\x00\x01\x00\x00"

    async def test_write_single_coil_build_response(self):
        """Test write single coil."""
        request = bit_msg.PDUwriteSingleCoil(0, address=2, bits=[True])
        result = await request.build_response(
            mock.AsyncMock(return_value=[True]), mock.AsyncMock(return_value=0)
        )
        assert result.to_bytes() == b"\x00\x02\xff\x00"

        request = bit_msg.PDUwriteSingleCoil(0, address=2, bits=[False])
        result = await request.build_response(
            mock.AsyncMock(return_value=[False]), mock.AsyncMock(return_value=0)
        )
        assert result.to_bytes() == b"\x00\x02\x00\x00"

    @pytest.mark.parametrize("value", [b"\x00\x01", b"\x00\xff", b"\xff\xff"])
    async def test_write_single_coil_illegal_value(self, value):
        """A value other than 0x0000 or 0xFF00 must answer 0x03 and leave the coil."""
        request = bit_msg.PDUwriteSingleCoil(0)
        request.from_bytes(0, b"\x00\x02" + value)
        result = await request.build_response(
            mock.AsyncMock(return_value=[True]), mock.AsyncMock(return_value=0)
        )
        assert result.function_code == 0x85
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

    @pytest.mark.parametrize(
        ("value", "bit"), [(b"\xff\x00", True), (b"\x00\x00", False)]
    )
    async def test_write_single_coil_legal_value(self, value, bit):
        """0xFF00 and 0x0000 are written as ON and OFF."""
        request = bit_msg.PDUwriteSingleCoil(1)
        request.from_bytes(0, b"\x00\x02" + value)
        x_set = mock.AsyncMock(return_value=0)
        result = await request.build_response(mock.AsyncMock(return_value=[bit]), x_set)
        assert result.to_bytes() == b"\x00\x02" + value
        x_set.assert_awaited_once_with(1, 5, 2, [bit])

    async def test_write_multiple_coils_build_response(self):
        """Test write multiple coils."""
        # too many values
        request = bit_msg.PDUwriteMultipleCoils(0, address=2, bits=[])
        result = await request.build_response(
            mock.AsyncMock(return_value=[True]), mock.AsyncMock(return_value=0)
        )

        # does not verify
        request = bit_msg.PDUwriteMultipleCoils(0, address=2, bits=[False] * 4)
        result = await request.build_response(
            mock.AsyncMock(return_value=[True]), mock.AsyncMock(return_value=0)
        )

        # verified request
        result = await request.build_response(
            mock.AsyncMock(return_value=[True]), mock.AsyncMock(return_value=0)
        )
        assert result.to_bytes() == b"\x00\x02\x00\x04"

    @pytest.mark.parametrize(
        ("request_pdu"),
        [
            bit_msg.PDUwriteSingleCoil(1, address=2, bits=[True]),
            bit_msg.PDUwriteMultipleCoils(1, address=2, bits=[True]),
        ],
    )
    async def test_write_coil_exception(self, request_pdu):
        """Test write single coil."""
        result = await request_pdu.build_response(
            mock.AsyncMock(return_value=1), mock.AsyncMock(return_value=1)
        )
        assert result.exception_code == 1

    def test_write_multiple_coils_response(self):
        """Test write multiple coils."""
        response = bit_msg.PDUwriteMultipleCoils(0, is_request=False)
        response.from_bytes(0, b"\x00\x80\x00\x08")
        assert response.address == 0x80
        assert response.count == 0x08

    def test_serializing_to_string(self):
        """Test serializing to string."""
        for pdu in (
            bit_msg.PDUwriteSingleCoil(0, address=1, bits=[True]),
            bit_msg.PDUwriteSingleCoil(0, is_request=False, address=1, bits=[True]),
            bit_msg.PDUwriteMultipleCoils(0, address=1, bits=[True] * 5),
            bit_msg.PDUwriteMultipleCoils(0, is_request=False, address=1, count=5),
        ):
            assert str(pdu)

    def test_pass_falsy_value_in_write_multiple_coils_request(self):
        """Test pass falsy value to write multiple coils."""
        request = bit_msg.PDUwriteMultipleCoils(0, address=1, bits=[False])
        assert request.bits == [False]
