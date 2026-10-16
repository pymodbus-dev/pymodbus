"""Test other messages."""

from typing import cast
from unittest import mock

import pytest

import pymodbus.pdu.other_message as pymodbus_message
from pymodbus.exceptions import ModbusIOException


class TestOtherMessage:
    """Unittest for the pymodbus.other_message module."""

    requests = [
        pymodbus_message.PDUreadExceptionStatus,
        pymodbus_message.PDUgetCommEventCounter,
        pymodbus_message.PDUgetCommEventLog,
        pymodbus_message.PDUreportDeviceId,
    ]

    responses = [
        pymodbus_message.PDUreadExceptionStatus(0, status=0x12),
        pymodbus_message.PDUgetCommEventCounter(0),
        pymodbus_message.PDUgetCommEventLog(0),
        pymodbus_message.PDUreportDeviceId(0, identifier=b"\x12"),
    ]

    def test_other_messages_to_string(self):
        """Test other messages to string."""
        for message in self.requests:
            assert str(message)
        for message2 in self.responses:
            assert str(message2)

    async def test_read_exception_status(self, mock_server_context):
        """Test read exception status."""
        context = mock_server_context()
        request = pymodbus_message.PDUreadExceptionStatus()
        request.x_decode(b"\x12")
        assert not request.x_encode()
        assert (await request.datastore_update(context, 0)).function_code == 0x07

        response = pymodbus_message.PDUreadExceptionStatus(status=0x12)
        assert response.x_encode() == b"\x12"
        response.x_decode(b"\x12")
        assert response.status == 0x12

    async def test_get_comm_event_counter(self, mock_server_context):
        """Test get comm event counter."""
        context = mock_server_context()
        request = pymodbus_message.PDUgetCommEventCounter(0)
        request.x_decode(b"\x12")
        assert not request.x_encode()
        assert (await request.datastore_update(context, 0)).function_code == 0x0B

        response = pymodbus_message.PDUgetCommEventCounter(0, count=0x12)
        assert response.x_encode() == b"\x00\x00\x00\x12"
        response.x_decode(b"\x00\x00\x00\x12")
        assert response.status
        assert response.count == 0x12

        response.status = False
        assert response.x_encode() == b"\xff\xff\x00\x12"

    async def test_get_comm_event_log(self, mock_server_context):
        """Test get comm event log."""
        context = mock_server_context()
        request = pymodbus_message.PDUgetCommEventLog()
        request.x_decode(b"\x12")
        assert not request.x_encode()
        assert (await request.datastore_update(context, 0)).function_code == 0x0C

        response = pymodbus_message.PDUgetCommEventLog()
        assert response.x_encode() == b"\x06\x00\x00\x00\x00\x00\x00"
        response.x_decode(b"\x06\x00\x00\x00\x12\x00\x12")
        assert response.status
        assert response.message_count == 0x12
        assert response.event_count == 0x12
        assert not response.events

        response.status = False
        assert response.x_encode() == b"\x06\xff\xff\x00\x12\x00\x12"

    def test_get_comm_event_log_with_events(self):
        """Test get comm event log with events."""
        response = pymodbus_message.PDUgetCommEventLog(events=[0x12, 0x34, 0x56])
        assert response.x_encode() == b"\x09\x00\x00\x00\x00\x00\x00\x12\x34\x56"
        response.x_decode(b"\x09\x00\x00\x00\x12\x00\x12\x12\x34\x56")
        assert response.status
        assert response.message_count == 0x12
        assert response.event_count == 0x12
        assert response.events == [0x12, 0x34, 0x56]

    async def test_report_device_id_request(self, mock_server_context):
        """Test report device_id request."""
        context = mock_server_context()
        with mock.patch("pymodbus.pdu.other_message.DeviceInformationFactory") as dif:
            # First test regular identity strings
            identity = {
                0x00: "VN",  # VendorName
                0x01: "PC",  # ProductCode
                0x02: "REV",  # MajorMinorRevision
                0x03: "VU",  # VendorUrl
                0x04: "PN",  # ProductName
                0x05: "MN",  # ModelName
                0x06: "UAN",  # UserApplicationName
                0x07: "RA",  # reserved
                0x08: "RB",  # reserved
            }
            dif.get.return_value = identity
            expected_identity = "-".join(identity.values()).encode()

            request = pymodbus_message.PDUreportDeviceId(0)
            response = await request.datastore_update(context, 1)
            assert (
                cast(pymodbus_message.PDUreportDeviceId, response).identifier
                == expected_identity
            )

            # Change to byte strings and test again (final result should be the same)
            identity2 = {
                0x00: b"VN",  # VendorName
                0x01: b"PC",  # ProductCode
                0x02: b"REV",  # MajorMinorRevision
                0x03: b"VU",  # VendorUrl
                0x04: b"PN",  # ProductName
                0x05: b"MN",  # ModelName
                0x06: b"UAN",  # UserApplicationName
                0x07: b"RA",  # reserved
                0x08: b"RB",  # reserved
            }
            dif.get.return_value = identity2

            request = pymodbus_message.PDUreportDeviceId()
            response = await request.datastore_update(context, 0)
            assert (
                cast(pymodbus_message.PDUreportDeviceId, response).identifier
                == expected_identity
            )

    async def test_report_device_id(self, mock_server_context):
        """Test report device_id."""
        context = mock_server_context()
        with mock.patch("pymodbus.pdu.other_message.DeviceInformationFactory") as dif:
            dif.get.return_value = {}
            request = pymodbus_message.PDUreportDeviceId()
            request.x_decode(b"\x12")
            assert not request.x_encode()
            assert (await request.datastore_update(context, 0)).function_code == 0x11

            response = pymodbus_message.PDUreportDeviceId(
                cast(
                    pymodbus_message.PDUreportDeviceId,
                    await request.datastore_update(context, 0),
                ).identifier,
                True,
            )

            assert response.x_encode() == b"\tPymodbus\xff"
            response.x_decode(b"\tPymodbus\xff")
            assert response.status
            assert response.identifier == b"Pymodbus"
            response.x_decode(b"\x03\x12\x00\x00")
            assert not response.status
            assert response.identifier == b"\x12\x00"

            response.status = False
            assert response.x_encode() == b"\x03\x12\x00\x00"

    def test_report_device_id_response_roundtrip(self):
        """Test decode( x_encode()) keeps identifier and status unchanged."""
        for identifier, status in ((b"Pymodbus", True), (b"\x12", False)):
            sent = pymodbus_message.PDUreportDeviceId(identifier, status)
            received = pymodbus_message.PDUreportDeviceId()
            received.x_decode(sent.x_encode())
            assert received.identifier == identifier
            assert received.status == status

    def test_report_device_id_response_invalid_byte_count(self):
        """Test byte count pointing outside the received data raises."""
        response = pymodbus_message.PDUreportDeviceId()
        for frame in (b"\x00\x12\xff", b"\x04\x12\xff"):
            with pytest.raises(ModbusIOException):
                response.x_decode(frame)
