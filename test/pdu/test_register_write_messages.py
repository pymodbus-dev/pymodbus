"""Test register write messages."""

from unittest import mock

import pytest

import pymodbus.pdu.register_message as pdu_reg
from pymodbus.constants import ExcCodes


# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class TestWriteRegisterMessages:
    """Register Message Test Fixture.

    This fixture tests the functionality of all the
    register based request/response messages:

    * Read/Write Input Registers
    * Read Holding Registers
    """

    def setup_method(self):
        """Initialize the test environment and builds request/result encoding pairs."""
        self.value = 0xABCD
        self.values = [0xA, 0xB, 0xC]
        self.write = {
            pdu_reg.PDUwriteSingleRegister(
                address=1, registers=[self.value]
            ): b"\x00\x01\xab\xcd",
            pdu_reg.PDUwriteSingleRegister(
                address=1, registers=[self.value]
            ): b"\x00\x01\xab\xcd",
            pdu_reg.PDUwriteMultipleRegisters(
                address=1, registers=self.values
            ): b"\x00\x01\x00\x03\x06\x00\x0a\x00\x0b\x00\x0c",
            pdu_reg.PDUwriteMultipleRegisters(
                address=1, registers=[0xD]
            ): b"\x00\x01\x00\x01\x02\x00\x0d",
            pdu_reg.PDUwriteMultipleRegisters(address=1, count=5): b"\x00\x01\x00\x05",
        }

    def test_register_write_requests_encode(self):
        """Test register write requests encode."""
        for request, response in iter(self.write.items()):
            assert request.to_bytes() == response

    def test_register_write_requests_decode(self):
        """Test register write requests decode."""
        addresses = [1, 1, 1, 1]
        values = sorted(
            self.write.items(),
            key=lambda x: str(x),  # pylint: disable=unnecessary-lambda
        )
        for packet, address in zip(values, addresses):
            request, response = packet
            request.from_bytes(0, response)
            assert request.address == address

    def test_invalid_write_multiple_registers_request(self):
        """Test invalid write multiple registers request."""
        request = pdu_reg.PDUwriteMultipleRegisters(address=0, registers=None)
        assert not request.registers

    @pytest.mark.parametrize(
        "frame",
        [
            b"\x00\x01\x00\x02\x02\x00\x0a",
            b"\x00\x01\x00\x01\x04\x00\x0a\x00\x0b",
            b"\x00\x01\x00\x01\x02\x00",
            b"\x00\x01\x00\x01\x02\x00\x0a\x00",
            b"\x00\x01\x00\x01\x01\x00",
        ],
    )
    async def test_write_multiple_registers_rejects_invalid_byte_count(self, frame):
        """Test inconsistent byte counts are rejected before writing."""
        request = pdu_reg.PDUwriteMultipleRegisters()
        request.from_bytes(0, frame)
        setValues = mock.AsyncMock()
        result = await request.build_response(mock.AsyncMock(), setValues)

        assert result.exception_code == ExcCodes.ILLEGAL_VALUE
        setValues.assert_not_awaited()

    async def test_write_multiple_registers_accepts_valid_byte_count(self):
        """Test a consistent byte count reaches the datastore."""
        request = pdu_reg.PDUwriteMultipleRegisters()
        request.from_bytes(0, b"\x00\x01\x00\x02\x04\x00\x0a\x00\x0b")
        setValues = mock.AsyncMock(return_value=0)
        result = await request.build_response(mock.AsyncMock(), setValues)

        assert result.count == 2
        setValues.assert_awaited_once_with(1, request.function_code, 1, [0x0A, 0x0B])

    def test_serializing_to_string(self):
        """Test serializing to string."""
        for request in iter(self.write.keys()):
            assert str(request)

    async def test_write_single_register_request(self):
        """Test write single register request."""
        request = pdu_reg.PDUwriteSingleRegister(address=0x00, registers=[0xF0000])
        result = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

        request.registers = [0x00FF]
        result = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        # assert result.exception_code == ExcCodes.ILLEGAL_ADDRESS

        # context.valid = True
        result = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.function_code == request.function_code

    async def test_write_multiple_register_request(self):
        """Test write multiple register request."""
        request = pdu_reg.PDUwriteMultipleRegisters(address=0x00, registers=[0x00] * 10)
        result = await request.build_response(mock.AsyncMock(), mock.AsyncMock())

        request.count = 0x800  # outside of range
        result = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

        # context.valid = True
        request = pdu_reg.PDUwriteMultipleRegisters(address=0x00, registers=[0x00] * 10)
        result = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.function_code == request.function_code

        request = pdu_reg.PDUwriteMultipleRegisters(address=0x00, registers=[0x00])
        result = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.function_code == request.function_code

    async def test_register_write_datastore_exceptions(self):
        """Test exception response from datastore."""
        getV = mock.AsyncMock(return_value=ExcCodes.ILLEGAL_VALUE)
        for pdu in (
            pdu_reg.PDUwriteSingleRegister(address=0x00, registers=[0xF000]),
            pdu_reg.PDUwriteMultipleRegisters(address=0x00, registers=[0x00] * 10),
            pdu_reg.PDUmaskWriteRegister(0x0000, 0x0101, 0x1010),
        ):
            await pdu.build_response(getV, mock.AsyncMock())

    def test_mask_write_register_request_encode(self):
        """Test basic bit message encoding/decoding."""
        handle = pdu_reg.PDUmaskWriteRegister(0x0000, 0x0101, 0x1010)
        result = handle.to_bytes()
        assert result == b"\x00\x00\x01\x01\x10\x10"

    def test_mask_write_register_request_decode(self):
        """Test basic bit message encoding/decoding."""
        request = b"\x00\x04\x00\xf2\x00\x25"
        handle = pdu_reg.PDUmaskWriteRegister()
        handle.from_bytes(0, request)
        assert handle.address == 0x0004
        assert handle.and_mask == 0x00F2
        assert handle.or_mask == 0x0025

    async def test_mask_write_register_request_build_response(
        self, MockLastValuesContext
    ):
        """Test write register request valid execution."""
        # The test uses the 4 nibbles of the 16-bit values to test
        # the combinations:
        #     and_mask=0, or_mask=0
        #     and_mask=F, or_mask=0
        #     and_mask=0, or_mask=F
        #     and_mask=F, or_mask=F
        context = MockLastValuesContext(valid=True, default=0xAA55)
        handle = pdu_reg.PDUmaskWriteRegister(0x0000, 0x0F0F, 0x00FF)
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(result, pdu_reg.PDUmaskWriteRegister)
        assert context.last_values == [0x0AF5]

    async def test_mask_write_register_request_invalid_build_response(self):
        """Test write register request build_response with invalid data."""
        handle = pdu_reg.PDUmaskWriteRegister(0x0000, -1, 0x1010)
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

        handle = pdu_reg.PDUmaskWriteRegister(0x0000, 0x0101, -1)
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.exception_code == ExcCodes.ILLEGAL_VALUE

        handle = pdu_reg.PDUmaskWriteRegister(0x0000, 0x0101, 0x1010)
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())

        # -----------------------------------------------------------------------#
        # Mask Write Register Response
        # -----------------------------------------------------------------------#

    def test_mask_write_register_response_encode(self):
        """Test basic bit message encoding/decoding."""
        handle = pdu_reg.PDUmaskWriteRegister(0x0000, 0x0101, 0x1010)
        result = handle.to_bytes()
        assert result == b"\x00\x00\x01\x01\x10\x10"

    def test_mask_write_register_frame_size(self):
        """Test that the read fifo queue response can decode."""
        assert pdu_reg.PDUmaskWriteRegister.calculatePduSize(True, 0, b"") == 10
        assert pdu_reg.PDUmaskWriteRegister.calculatePduSize(False, 0, b"") == 10

    def test_mask_write_register_response_decode(self):
        """Test basic bit message encoding/decoding."""
        request = b"\x00\x04\x00\xf2\x00\x25"
        handle = pdu_reg.PDUmaskWriteRegister()
        handle.from_bytes(0, request)
        assert handle.address == 0x0004
        assert handle.and_mask == 0x00F2
        assert handle.or_mask == 0x0025

    @pytest.mark.parametrize(
        ("request_pdu"),
        [
            pdu_reg.PDUwriteSingleRegister(0, address=0x00, registers=[5]),
            pdu_reg.PDUwriteMultipleRegisters(0, address=0x00, registers=[0x00] * 10),
            pdu_reg.PDUmaskWriteRegister(0, 0x0000, 0x01, 0x1010),
        ],
    )
    async def test_register_write_exception(self, request_pdu, mock_server_context):
        """Test write single coil."""
        result = await request_pdu.build_response(
            mock.AsyncMock(), mock.AsyncMock(return_value=1)
        )
        assert result.exception_code == 1
