"""Bit Message Test Fixture.

This fixture tests the functionality of all the
bit based request/response messages:

* Read/Write Discretes
* Read Coils
"""

import pytest

import pymodbus.pdu.file_message as file_msg
from pymodbus.exceptions import ModbusException


TEST_MESSAGE = b"\x00\n\x00\x04\x00\x01\x00\x02\x00\x03\x00\x04"


class TestBitMessage:
    """Modbus bit message tests."""

    def test_read_fifo_queue_request_encode(self):
        """Test basic bit message encoding/decoding."""
        handle = file_msg.PDUreadFifoQueue(0x1234)
        result = handle.x_encode()
        assert result == b"\x12\x34"

    def test_read_fifo_queue_request_decode(self):
        """Test basic bit message encoding/decoding."""
        handle = file_msg.PDUreadFifoQueue(0x0000)
        handle.x_decode(b"\x12\x34")
        assert handle.address == 0x1234

    async def test_read_fifo_queue_request(self, mock_server_context):
        """Test basic bit message encoding/decoding."""
        context = mock_server_context()
        handle = file_msg.PDUreadFifoQueue(0x1234)
        result = await handle.datastore_update(context, 0)
        assert isinstance(result, file_msg.PDUreadFifoQueue)

    def test_read_fifo_queue_response_encode(self):
        """Test that the read fifo queue response can encode."""
        message = TEST_MESSAGE
        handle = file_msg.PDUreadFifoQueue([1, 2, 3, 4])
        result = handle.x_encode()
        assert result == message

    def test_read_fifo_queue_response_decode(self):
        """Test that the read fifo queue response can decode."""
        message = TEST_MESSAGE
        handle = file_msg.PDUreadFifoQueue([1, 2, 3, 4])
        handle.x_decode(message)
        assert handle.values == [1, 2, 3, 4]

    def test_frame_size(self):
        """Test that the read fifo queue response can decode."""
        message = TEST_MESSAGE
        assert (
            file_msg.PDUreadFifoQueue.x_calculateRtuFrameSize(b"\x00\x18" + message)
            == 14
        )
        assert file_msg.PDUreadFifoQueue.x_calculateRtuFrameSize(b"") == 6

    # -----------------------------------------------------------------------#
    #  File Record
    # -----------------------------------------------------------------------#

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
        handle = file_msg.PDUreadFileRecord(records=records)
        result = handle.x_encode()
        assert result == b"\x07\x06\x00\x01\x00\x02\x00\x00"

    def test_read_file_record_request_decode(self):
        """Test basic bit message encoding/decoding."""
        # record = FileRecord(file_number=0x04, record_number=0x01, record_length=0x02)
        request = b"\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02"
        handle = file_msg.PDUreadFileRecord()
        handle.x_decode(request)
        # assert handle.records[0] == record

    def test_read_file_record_request_frame_size(self):
        """Test basic bit message encoding/decoding."""
        request = (
            b"\x00\x00\x0e\x06\x00\x04\x00\x01\x00\x02\x06\x00\x03\x00\x09\x00\x02"
        )
        handle = file_msg.PDUreadFileRecord()
        size = handle.x_calculateRtuFrameSize(request)
        assert size == 0x0E + 5

    async def test_read_file_record_request_datastore_update(self, mock_server_context):
        """Test basic bit message encoding/decoding."""
        handle = file_msg.PDUreadFileRecord()
        result = await handle.datastore_update(mock_server_context(), 0)
        assert isinstance(result, file_msg.PDUreadFileRecord)

    # -----------------------------------------------------------------------#
    #  Read File Record Response
    # -----------------------------------------------------------------------#

    def test_read_file_record_response_encode(self):
        """Test basic bit message encoding/decoding."""
        records = [file_msg.FileRecord(record_data=b"\x00\x01\x02\x03\x04\x05")]
        handle = file_msg.PDUreadFileRecord(records)
        result = handle.x_encode()
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
        handle = file_msg.PDUreadFileRecord()
        handle.x_decode(response)

        # assert handle.records[0] == record1
        # ssert handle.records[1] == record2

    def test_read_file_record_response_frame_size(self):
        """Test basic bit message encoding/decoding."""
        request = b"\x00\x00\x0c\x05\x06\x0d\xfe\x00\x20\x05\x05\x06\x33\xcd\x00\x40"
        handle = file_msg.PDUreadFileRecord()
        size = handle.x_calculateRtuFrameSize(request)
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
        handle = file_msg.PDUwriteFileRecord(records)
        result = handle.x_encode()
        assert result == b"\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03"

    def test_write_file_record_request_decode(self):
        """Test basic bit message encoding/decoding."""
        # record = FileRecord(
        #     file_number=0x04,
        #     record_number=0x07,
        #     record_data=b"\x06\xaf\x04\xbe\x10\x0d",
        # )
        request = b"\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = file_msg.PDUwriteFileRecord()
        handle.x_decode(request)
        # assert handle.records[0] == record

    def test_write_file_record_request_frame_size(self):
        """Test write file record request rtu frame size calculation."""
        request = b"\x00\x00\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = file_msg.PDUwriteFileRecord()
        size = handle.x_calculateRtuFrameSize(request)
        assert size == 0x0D + 5

    async def test_write_file_record_request_datastore_update(
        self, mock_server_context
    ):
        """Test basic bit message encoding/decoding."""
        handle = file_msg.PDUwriteFileRecord()
        result = await handle.datastore_update(mock_server_context(), 0)
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
        handle = file_msg.PDUwriteFileRecord(records)
        result = handle.x_encode()
        assert result == b"\x0b\x06\x00\x01\x00\x02\x00\x02\x00\x01\x02\x03"

    def test_write_file_record_response_decode(self):
        """Test basic bit message encoding/decoding."""
        # record = FileRecord(
        #     file_number=0x04,
        #     record_number=0x07,
        #     record_data=b"\x06\xaf\x04\xbe\x10\x0d",
        # )
        request = b"\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = file_msg.PDUwriteFileRecord()
        handle.x_decode(request)
        # assert handle.records[0] == record

    def test_read_file_record_request_decode_invalid_byte_count(self):
        """Test file_msg.PDUreadFileRecord raises ModbusException on oversized byte_count."""
        handle = file_msg.PDUreadFileRecord()
        with pytest.raises(ModbusException):
            handle.x_decode(bytes([0xFF, 0x06, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01]))

    def test_write_file_record_request_decode_invalid_byte_count(self):
        """Test file_msg.PDUwriteFileRecord raises ModbusException on oversized byte_count."""
        handle = file_msg.PDUwriteFileRecord()
        with pytest.raises(ModbusException):
            handle.x_decode(
                bytes([0xFF, 0x06, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00])
            )

    def test_read_fifo_queue_response_decode_invalid_count(self):
        """Test file_msg.PDUreadFifoQueue raises ModbusException on oversized count."""
        handle = file_msg.PDUreadFifoQueue()
        with pytest.raises(ModbusException):
            handle.x_decode(bytes([0x00, 0x00, 0xFF, 0xFF]))

    def test_write_file_record_response_frame_size(self):
        """Test write file record response rtu frame size calculation."""
        request = b"\x00\x00\x0d\x06\x00\x04\x00\x07\x00\x03\x06\xaf\x04\xbe\x10\x0d"
        handle = file_msg.PDUwriteFileRecord()
        size = handle.x_calculateRtuFrameSize(request)
        assert size == 0x0D + 5
