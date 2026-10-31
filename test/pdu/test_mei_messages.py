"""MEI Message Test Fixture.

This fixture tests the functionality of all the
mei based request/response messages:
"""

from typing import cast
from unittest import mock

import pytest

from pymodbus.constants import DeviceInformation, ExcCodes
from pymodbus.pdu import DecodePDU, ModbusControlBlock, PDUexception
from pymodbus.pdu.mei_message import PDUreadDeviceInformation


TEST_VERSION = b"v2.1.12"
TEST_MESSAGE = b"\x00\x07Company\x01\x07Product\x02\x07v2.1.12"


class TestMeiMessage:
    """Unittest for the pymodbus.mei_message module."""

    # -----------------------------------------------------------------------#
    #  Read Device Information
    # -----------------------------------------------------------------------#

    def test_read_device_information_request_encode(self):
        """Test basic bit message encoding/decoding."""
        params = {"read_code": int(DeviceInformation.BASIC), "object_id": 0x00}
        handle = PDUreadDeviceInformation(0, *params)
        result = handle.to_bytes()
        assert result == b"\x0e\x01\x00"
        assert "PDUreadDeviceInformation" in str(handle)

    def test_read_device_information_request_decode(self):
        """Test basic bit message encoding/decoding."""
        handle = PDUreadDeviceInformation(0)
        handle.from_bytes(0, b"\x0e\x01\x00")
        assert handle.read_code == DeviceInformation.BASIC
        assert not handle.object_id

    def test_device_information_mei_type_is_routed(self):
        """Test MEI type 0x0E is routed to device identification."""
        pdu = DecodePDU(True).decode(b"\x2b\x0e\x01\x00")
        assert isinstance(pdu, PDUreadDeviceInformation)

    async def test_read_device_information_request(self, mock_server_context):
        """Test basic bit message encoding/decoding."""
        control = ModbusControlBlock()
        control.Identity.VendorName = "Company"
        control.Identity.ProductCode = "Product"
        control.Identity.MajorMinorRevision = TEST_VERSION
        control.Identity.update({0x81: ["Test", "Repeated"]})

        handle = PDUreadDeviceInformation()
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert isinstance(result, PDUreadDeviceInformation)
        assert result.information[0x00] == "Company"
        assert result.information[0x01] == "Product"
        assert result.information[0x02] == TEST_VERSION
        with pytest.raises(KeyError):
            _ = result.information[0x81]

        handle = PDUreadDeviceInformation(
            read_code=DeviceInformation.SPECIFIC, object_id=0x00
        )
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert cast(PDUreadDeviceInformation, result).information == {0x00: "Company"}

        handle = PDUreadDeviceInformation(
            read_code=DeviceInformation.EXTENDED, object_id=0x80
        )
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert cast(PDUreadDeviceInformation, result).information[0x81] == [
            "Test",
            "Repeated",
        ]

    async def test_read_device_information_request_error(self, mock_server_context):
        """Test basic bit message encoding/decoding."""
        handle = PDUreadDeviceInformation()
        handle.read_code = -1
        assert (
            await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0xAB
        handle.read_code = 0x05
        assert (
            await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0xAB
        handle.object_id = -1
        assert (
            await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0xAB
        handle.object_id = 0x100
        assert (
            await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        ).function_code == 0xAB
        handle = PDUreadDeviceInformation(
            read_code=DeviceInformation.SPECIFIC, object_id=0x54
        )
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.exception_code == ExcCodes.ILLEGAL_ADDRESS
        ModbusControlBlock().Identity[0xFE] = ""
        handle = PDUreadDeviceInformation(
            read_code=DeviceInformation.SPECIFIC, object_id=0xFE
        )
        result = await handle.build_response(mock.AsyncMock(), mock.AsyncMock())
        assert result.exception_code == ExcCodes.ILLEGAL_ADDRESS

    def test_read_device_information_calc1(self):
        """Test calculatePduSize, short buffer."""
        handle = PDUreadDeviceInformation()
        assert handle.calculatePduSize(True, 0, b"\x0e\x01\x83") == 999
        assert (
            handle.calculatePduSize(False, 0, b"\x0e\x01\x83\x00\x00\x03\x01\x03")
            == 998
        )

    def test_read_device_information_sub_fc(self):
        """Test calculatePduSize, short buffer."""
        handle = PDUreadDeviceInformation()
        assert handle.decode_sub_function_code(0, b"\x0e\x01\x83") == 0x83
        handle2 = PDUreadDeviceInformation()
        assert handle2.decode_sub_function_code(0, b"\x0e\x01\x83") == 0x83

    def test_read_device_information_encode(self):
        """Test that the read fifo queue response can encode."""
        message = b"\x0e\x01\x83\x00\x00\x03"
        message += TEST_MESSAGE
        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
        }
        handle = PDUreadDeviceInformation(
            read_code=DeviceInformation.BASIC, information=dataset
        )
        result = handle.to_bytes()
        assert result == message
        assert "PDUreadDeviceInformation" in str(handle)

        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
            0x81: ["Test", "Repeated"],
            0x82: PDUexception(0, 0x01, 0),
        }
        message = b"\x0e\x03\x83\x00\x00\x06"
        message += TEST_MESSAGE
        message += b"\x81\x04Test\x81\x08Repeated\x82\x01\x00"
        handle = PDUreadDeviceInformation(
            read_code=DeviceInformation.EXTENDED, information=dataset
        )
        result = handle.to_bytes()
        assert result == message

    def test_read_device_information_encode_long(self):
        """Test that the read fifo queue response can encode."""
        longstring = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing "
            "elit. Vivamus rhoncus massa turpis, sit amet ultrices"
            " orci semper ut. Aliquam tristique sapien in lacus "
            "pharetra, in convallis nunc consectetur. Nunc velit "
            "elit, vehicula tempus tempus sed. "
        )

        message = b"\x0e\x01\x83\xff\x80\x03"
        message += TEST_MESSAGE
        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
            0x80: longstring,
        }
        handle = PDUreadDeviceInformation(
            read_code=DeviceInformation.BASIC, information=dataset
        )
        result = handle.to_bytes()
        assert result == message
        assert "PDUreadDeviceInformation" in str(handle)

    def test_read_device_information_decode(self):
        """Test that the read device information response can decode."""
        message = b"\x0e\x01\x01\x00\x00\x05"
        message += TEST_MESSAGE
        message += b"\x81\x04Test\x81\x08Repeated\x81\x07Another"
        handle = PDUreadDeviceInformation(read_code=0x00, information={})
        handle.from_bytes(0, message)
        assert handle.read_code == DeviceInformation.BASIC
        assert handle.conformity == 0x01
        assert handle.information[0x00] == b"Company"
        assert handle.information[0x01] == b"Product"
        assert handle.information[0x02] == TEST_VERSION
        assert handle.information[0x81] == [b"Test", b"Repeated", b"Another"]

    def test_frame_size(self):
        """Test that the read device information response can decode."""
        message = (
            b"\x04\x2b\x0e\x01\x81\x00\x01\x01\x00\x06\x66\x6f\x6f\x62\x61\x72\xd7\x3b"
        )
        result = PDUreadDeviceInformation.calculatePduSize(True, 0, message)
        assert result == 18
        message = b"\x00\x2b\x0e\x02\x00\x4d\x47"
        result = PDUreadDeviceInformation.calculatePduSize(False, 0, message)
        assert result == 7
