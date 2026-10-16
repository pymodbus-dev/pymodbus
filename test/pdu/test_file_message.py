"""Bit Message Test Fixture.

This fixture tests the functionality of all the
bit based request/response messages:

* Read/Write Discretes
* Read Coils
"""

from unittest import mock

import pytest

import pymodbus.pdu.file_message as file_msg
from pymodbus.exceptions import ModbusException, ModbusIOException
from pymodbus.pdu import DecodePDU


class TestFileMessage:
    """Modbus bit message tests."""

    def test_file_record_length(self):
        """Test file record length generation."""
        record = file_msg.FileRecord(
            file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x04"
        )
        assert record.record_length == 0x02

    def test_file_record_errors(self):
        """Test file record length generation."""
        with pytest.raises(ModbusException):
            file_msg.FileRecord(record_length=12, record_data=b"\x00\x01\x02\x04")
        with pytest.raises(ModbusException):
            file_msg.FileRecord(record_length=11)

    def test_read_file_record_request_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [file_msg.FileRecord(file_number=0x01, record_number=0x02)]
        handle = file_msg.PDUreadFileRecord(0, records=records)
        result = handle.to_bytes()
        assert result == b"\x07\x06\x00\x01\x00\x02\x00\x00"

    def test_read_file_record_request_decode(self):
        """Test basic bit message encoding/decoding."""
        request = b"\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02"
        handle = file_msg.PDUreadFileRecord(0)
        handle.from_bytes(0, request)

    def test_read_file_record_request_frame_size(self):
        """Test basic bit message encoding/decoding."""
        request = (
            b"\x00\x00\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02"
        )
        handle = file_msg.PDUreadFileRecord(0)
        size = handle.calculatePduSize(True, 0, request)
        assert size == 0x0E + 5

    async def test_read_file_record_request_build_response(self):
        """Test basic bit message encoding/decoding."""
        handle = file_msg.PDUreadFileRecord(0)
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(result, file_msg.PDUreadFileRecord)

    # -----------------------------------------------------------------------#
    #  Read File Record Response
    # -----------------------------------------------------------------------#

    def test_read_file_record_response_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [file_msg.FileRecord(record_data=b"\x00\x01\x02\x03\x04\x05")]
        handle = file_msg.PDUreadFileRecord(0, is_request=False, records=records)
        result = handle.to_bytes()
        assert result == b"\x08\x07\x06\x00\x01\x02\x03\x04\x05"

    def test_read_file_record_response_decode(self):
        """Test basic bit message encoding/decoding."""
        # record1 = FileRecord(
        #     file_number=0x00, record_number=0x00, record_data=b"\x0d\xfe\x00\x20"
        # )
        # record2 = FileRecord(
        #     file_number=0x00, record_number=0x00, record_data=b"\x33\xcd\x00\x40"
        # )
        response = b"\x0c\x05\x06\x0d\xfe\x00\x20\x05\x06\x33\xcd\x00\x40"
        handle = file_msg.PDUreadFileRecord(0, is_request=False)
        handle.from_bytes(0, response)

        # assert handle.records[0] == record1
        # ssert handle.records[1] == record2

    def test_read_file_record_response_frame_size(self):
        """Test basic bit message encoding/decoding."""
        request = b"\x00\x00\x0c\x05\x06\x0d\xfe\x00\x20\x05\x05\x06\x33\xcd\x00\x40"
        handle = file_msg.PDUreadFileRecord(0)
        size = handle.calculatePduSize(True, 0, request)
        assert size == 0x0C + 5

    # -----------------------------------------------------------------------#
    #  Write File Record Request
    # -----------------------------------------------------------------------#

    def test_write_file_record_request_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [
            file_msg.FileRecord(
                file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x03"
            )
        ]
        handle = file_msg.PDUwriteFileRecord(0, is_request=False, records=records)
        result = handle.to_bytes()
        assert result == b"\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03"

    def test_write_file_record_request_decode(self):
        """Test basic bit message encoding/decoding."""
        # record = FileRecord(
        #     file_number=0x04,
        #     record_number=0x07,
        #     record_data=b"\x06\xaf\x04\xbe\x10\x0d",
        # )
        request = b"\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = file_msg.PDUwriteFileRecord(0)
        handle.from_bytes(0, request)
        # assert handle.records[0] == record

    def test_write_file_record_request_frame_size(self):
        """Test write file record request rtu frame size calculation."""
        request = b"\x00\x00\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = file_msg.PDUwriteFileRecord(0)
        size = handle.calculatePduSize(True, 0, request)
        assert size == 0x0D + 5

    async def test_write_file_record_request_build_response(self):
        """Test basic bit message encoding/decoding."""
        handle = file_msg.PDUwriteFileRecord(0)
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(result, file_msg.PDUwriteFileRecord)

    # -----------------------------------------------------------------------#
    #  Write File Record Response
    # -----------------------------------------------------------------------#

    def test_write_file_record_response_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [
            file_msg.FileRecord(
                file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x03"
            )
        ]
        handle = file_msg.PDUwriteFileRecord(0, is_request=False, records=records)
        result = handle.to_bytes()
        assert result == b"\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03"

    def test_write_file_record_response_decode(self):
        """Test basic bit message encoding/decoding."""
        # record = FileRecord(
        #     file_number=0x04,
        #     record_number=0x07,
        #     record_data=b"\x06\xaf\x04\xbe\x10\x0d",
        # )
        request = b"\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = file_msg.PDUwriteFileRecord(0)
        handle.from_bytes(0, request)
        # assert handle.records[0] == record

    def test_read_file_record_request_decode_invalid_byte_count(self):
        """Test file_msg.PDUreadFileRecord raises ModbusException on oversized byte_count."""
        handle = file_msg.PDUreadFileRecord(0)
        with pytest.raises(ModbusException):
            handle.from_bytes(
                0, bytes([0xFF, 0x06, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01])
            )

    def test_write_file_record_request_decode_invalid_byte_count(self):
        """Test file_msg.PDUwriteFileRecord raises ModbusException on oversized byte_count."""
        handle = file_msg.PDUwriteFileRecord(0)
        with pytest.raises(ModbusException):
            handle.from_bytes(
                0, bytes([0xFF, 0x06, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00])
            )

    def test_read_fifo_queue_response_decode_invalid_count(self):
        """Test file_msg.PDUreadFifoQueue raises ModbusException on oversized count."""
        handle = file_msg.PDUreadFifoQueue(0, is_request=False)
        with pytest.raises(ModbusException):
            handle.from_bytes(0, bytes([0x00, 0x00, 0xFF, 0xFF]))

    def test_write_file_record_response_frame_size(self):
        """Test write file record response rtu frame size calculation."""
        request = b"\x00\x00\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = file_msg.PDUwriteFileRecord(0)
        size = handle.calculatePduSize(True, 0, request)
        assert size == 0x0D + 5

    server = DecodePDU(True)
    client = DecodePDU(False)

    @pytest.mark.parametrize(
        ("decoder", "frame"),
        [
            (server, b"\x14\x10"),  # read file record, byte count past the frame
            (server, b"\x15\x10"),  # write file record, byte count past the frame
            (client, b"\x18\x00\x06\x00\x05\x00\x01"),  # fifo count past the frame
        ],
    )
    def test_decode_bad_file_record_frame(self, decoder, frame):
        """Test bad file record frames fail like other undecodable frames."""
        with pytest.raises(ModbusIOException):
            decoder.decode(frame)
