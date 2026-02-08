"""Bit Message Test Fixture.

This fixture tests the functionality of all the
bit based request/response messages:

* Read/Write Discretes
* Read Coils
"""
import pytest

from pymodbus.exceptions import ModbusException
from pymodbus.pdu.file_message import (
    FileRecord,
    ReadFifoQueueRequest,
    ReadFifoQueueResponse,
    ReadFileRecordRequest,
    ReadFileRecordResponse,
    WriteFileRecordRequest,
    WriteFileRecordResponse,
)


TEST_MESSAGE = b"\x00\n\x00\x04\x00\x01\x00\x02\x00\x03\x00\x04"

class TestBitMessage:
    """Modbus bit message tests."""

    def test_read_fifo_queue_request_encode(self):
        """Test basic bit message encoding/decoding."""
        handle = ReadFifoQueueRequest(0x1234)
        result = handle.encode()
        assert result == b"\x12\x34"

    def test_read_fifo_queue_request_decode(self):
        """Test basic bit message encoding/decoding."""
        handle = ReadFifoQueueRequest(0x0000)
        handle.decode(b"\x12\x34")
        assert handle.address == 0x1234

    async def test_read_fifo_queue_request(self, mock_server_context):
        """Test basic bit message encoding/decoding."""
        context = mock_server_context()
        handle = ReadFifoQueueRequest(0x1234)
        result = await handle.datastore_update(context, 0)
        assert isinstance(result, ReadFifoQueueResponse)

    def test_read_fifo_queue_response_encode(self):
        """Test that the read fifo queue response can encode."""
        message = TEST_MESSAGE
        handle = ReadFifoQueueResponse([1, 2, 3, 4])
        result = handle.encode()
        assert result == message

    def test_read_fifo_queue_response_decode(self):
        """Test that the read fifo queue response can decode."""
        message = TEST_MESSAGE
        handle = ReadFifoQueueResponse([1, 2, 3, 4])
        handle.decode(message)
        assert handle.values == [1, 2, 3, 4]

    def test_frame_size(self):
        """Test that the read fifo queue response can decode."""
        message = TEST_MESSAGE
        result = ReadFifoQueueResponse.calculateRtuFrameSize(message)
        assert result == 14

    # -----------------------------------------------------------------------#
    #  File Record
    # -----------------------------------------------------------------------#

    def test_file_record_length(self):
        """Test file record length generation."""
        record = FileRecord(
            file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x04"
        )
        assert record.record_length == 0x02

    def test_file_record_errors(self):
        """Test file record length generation."""
        with pytest.raises(ModbusException):
            FileRecord(record_length=12, record_data=b"\x00\x01\x02\x04")
        with pytest.raises(ModbusException):
            FileRecord(record_length=11)

    def test_read_file_record_request_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [FileRecord(file_number=0x01, record_number=0x02)]
        handle = ReadFileRecordRequest(records=records)
        result = handle.encode()
        assert result == b"\x07\x06\x00\x01\x00\x02\x00\x00"

    def test_read_file_record_request_decode(self):
        """Test basic bit message encoding/decoding."""
        # record = FileRecord(file_number=0x04, record_number=0x01, record_length=0x02)
        request = b"\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02"
        handle = ReadFileRecordRequest()
        handle.decode(request)
        # assert handle.records[0] == record

    def test_read_file_record_request_frame_size(self):
        """Test basic bit message encoding/decoding."""
        request = (
            b"\x00\x00\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02"
        )
        handle = ReadFileRecordRequest()
        size = handle.calculateRtuFrameSize(request)
        assert size == 0x0E + 5

    async def test_read_file_record_request_datastore_update(self, mock_server_context):
        """Test basic bit message encoding/decoding."""
        handle = ReadFileRecordRequest()
        result = await handle.datastore_update(mock_server_context(), 0)
        assert isinstance(result, ReadFileRecordResponse)

    # -----------------------------------------------------------------------#
    #  Read File Record Response
    # -----------------------------------------------------------------------#

    def test_read_file_record_response_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [FileRecord(record_data=b"\x00\x01\x02\x03\x04\x05")]
        handle = ReadFileRecordResponse(records)
        result = handle.encode()
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
        handle = ReadFileRecordResponse()
        handle.decode(response)

        # assert handle.records[0] == record1
        # ssert handle.records[1] == record2

    def test_read_file_record_response_frame_size(self):
        """Test basic bit message encoding/decoding."""
        request = b"\x00\x00\x0c\x05\x06\x0d\xfe\x00\x20\x05\x05\x06\x33\xcd\x00\x40"
        handle = ReadFileRecordResponse()
        size = handle.calculateRtuFrameSize(request)
        assert size == 0x0C + 5

    # -----------------------------------------------------------------------#
    #  Write File Record Request
    # -----------------------------------------------------------------------#

    def test_write_file_record_request_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [
            FileRecord(
                file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x03"
            )
        ]
        handle = WriteFileRecordRequest(records)
        result = handle.encode()
        assert result == b"\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03"

    def test_write_file_record_request_decode(self):
        """Test basic bit message encoding/decoding."""
        # record = FileRecord(
        #     file_number=0x04,
        #     record_number=0x07,
        #     record_data=b"\x06\xaf\x04\xbe\x10\x0d",
        # )
        request = b"\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = WriteFileRecordRequest()
        handle.decode(request)
        # assert handle.records[0] == record

    def test_write_file_record_request_frame_size(self):
        """Test write file record request rtu frame size calculation."""
        request = b"\x00\x00\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = WriteFileRecordRequest()
        size = handle.calculateRtuFrameSize(request)
        assert size == 0x0D + 5

    async def test_write_file_record_request_datastore_update(self, mock_server_context):
        """Test basic bit message encoding/decoding."""
        handle = WriteFileRecordRequest()
        result = await handle.datastore_update(mock_server_context(), 0)
        assert isinstance(result, WriteFileRecordResponse)

    # -----------------------------------------------------------------------#
    #  Write File Record Response
    # -----------------------------------------------------------------------#

    def test_write_file_record_response_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [
            FileRecord(
                file_number=0x01, record_number=0x02, record_data=b"\x00\x01\x02\x03"
            )
        ]
        handle = WriteFileRecordResponse(records)
        result = handle.encode()
        assert result == b"\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03"

    def test_write_file_record_response_decode(self):
        """Test basic bit message encoding/decoding."""
        # record = FileRecord(
        #     file_number=0x04,
        #     record_number=0x07,
        #     record_data=b"\x06\xaf\x04\xbe\x10\x0d",
        # )
        request = b"\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = WriteFileRecordResponse()
        handle.decode(request)
        # assert handle.records[0] == record

    def test_write_file_record_response_frame_size(self):
        """Test write file record response rtu frame size calculation."""
        request = b"\x00\x00\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = WriteFileRecordResponse()
        size = handle.calculateRtuFrameSize(request)
        assert size == 0x0D + 5
