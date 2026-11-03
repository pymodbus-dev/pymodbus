"""Test other messages."""

from typing import cast
from unittest import mock

import pytest

import pymodbus.pdu.other_message as pymodbus_message
from pymodbus.exceptions import ModbusIOException


class TestOtherMessage:
    """Unittest for the pymodbus.other_message module."""

    async def test_read_exception_status(self):
        """Test read exception status."""
        request = pymodbus_message.PDUreadExceptionStatus(0)
        request.from_bytes(0, b"\x12")
        assert not request.to_bytes()
        assert (
            await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0x07

        response = pymodbus_message.PDUreadExceptionStatus(
            0, is_request=False, status=0x12
        )
        assert response.to_bytes() == b"\x12"
        response.from_bytes(0, b"\x12")
        assert response.status == 0x12

    async def test_get_comm_event_counter(self):
        """Test get comm event counter."""
        request = pymodbus_message.PDUgetCommEventCounter(0)
        request.from_bytes(1, b"\x0b\x00\x00\x00\x12")
        assert not request.to_bytes()
        assert (
            await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0x0B

        response = pymodbus_message.PDUgetCommEventCounter(
            0, is_request=False, count=0x12
        )
        assert response.to_bytes() == b"\x00\x00\x00\x12"
        response.from_bytes(0, b"\x00\x00\x00\x12")
        assert response.status
        assert response.count == 0x12

        response.status = False
        assert response.to_bytes() == b"\xff\xff\x00\x12"

    async def test_get_comm_event_log(self):
        """Test get comm event log."""
        request = pymodbus_message.PDUgetCommEventLog(0)
        request.from_bytes(0, b"\x12")
        assert not request.to_bytes()
        assert (
            await request.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0x0C

        response = pymodbus_message.PDUgetCommEventLog(0, is_request=False)
        assert response.to_bytes() == b"\x06\x00\x00\x00\x00\x00\x00"
        response.from_bytes(0, b"\x06\x00\x00\x00\x12\x00\x12")
        assert response.status
        assert response.message_count == 0x12
        assert response.event_count == 0x12
        assert not response.events

        response.status = False
        assert response.to_bytes() == b"\x06\xff\xff\x00\x12\x00\x12"

    def test_get_comm_event_log_with_events(self):
        """Test get comm event log with events."""
        response = pymodbus_message.PDUgetCommEventLog(
            0, is_request=False, events=[0x12, 0x34, 0x56]
        )
        assert response.to_bytes() == b"\x09\x00\x00\x00\x00\x00\x00\x12\x34\x56"
        response.from_bytes(0, b"\x09\x00\x00\x00\x12\x00\x12\x12\x34\x56")
        assert response.status
        assert response.message_count == 0x12
        assert response.event_count == 0x12
        assert response.events == [0x12, 0x34, 0x56]

    async def test_report_device_id_request(self):
        """Test report device_id request."""
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
            response = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
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

            request = pymodbus_message.PDUreportDeviceId(0)
            response = await request.build_response(mock.AsyncMock(), mock.AsyncMock())
            assert (
                cast(pymodbus_message.PDUreportDeviceId, response).identifier
                == expected_identity
            )

    async def test_report_device_id(self):
        """Test report device_id."""
        with mock.patch("pymodbus.pdu.other_message.DeviceInformationFactory") as dif:
            dif.get.return_value = {}
            request = pymodbus_message.PDUreportDeviceId(0)
            request.from_bytes(0, b"\x12")
            assert not request.to_bytes()
            assert (
                await request.build_response(mock.AsyncMock(), mock.AsyncMock())
            ).function_code == 0x11

            response = pymodbus_message.PDUreportDeviceId(
                0,
                is_request=False,
                identifier=cast(
                    pymodbus_message.PDUreportDeviceId,
                    await request.build_response(mock.AsyncMock(), mock.AsyncMock()),
                ).identifier,
                status=True,
            )

            assert response.to_bytes() == b"\tPymodbus\xff"
            response.from_bytes(0, b"\tPymodbus\xff")
            assert response.status
            assert response.identifier == b"Pymodbus"
            response.from_bytes(0, b"\x03\x12\x00\x00")
            assert response.identifier == b"\x12\x00"
            response.status = False
            assert response.to_bytes() == b"\x03\x12\x00\x00"

    def test_report_device_id_response_roundtrip(self):
        """Test decode( to_bytes()) keeps identifier and status unchanged."""
        for identifier, status in ((b"Pymodbus", True), (b"\x12", False)):
            sent = pymodbus_message.PDUreportDeviceId(
                0, is_request=False, identifier=identifier, status=status
            )
            received = pymodbus_message.PDUreportDeviceId(0, is_request=False)
            received.from_bytes(0, sent.to_bytes())
            assert received.identifier == identifier
            assert received.status == status

    def test_report_device_id_response_invalid_byte_count(self):
        """Test byte count pointing outside the received data raises."""
        response = pymodbus_message.PDUreportDeviceId(0, is_request=False)
        for frame in (b"\x00\x12\xff", b"\x04\x12\xff"):
            with pytest.raises(ModbusIOException):
                response.from_bytes(0, frame)
