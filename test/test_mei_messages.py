"""MEI Message Test Fixture.

This fixture tests the functionality of all the
mei based request/response messages:
"""
import unittest

from pymodbus.constants import DeviceInformation
from pymodbus.device import ModbusControlBlock
from pymodbus.mei_message import (
    ReadDeviceInformationRequest,
    ReadDeviceInformationResponse,
)


# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#

TEST_VERSION = b"v2.1.12"
TEST_MESSAGE = b"\x00\x07Company\x01\x07Product\x02\x07v2.1.12"


class ModbusMeiMessageTest(unittest.TestCase):
    """Unittest for the pymodbus.mei_message module."""

    # -----------------------------------------------------------------------#
    #  Read Device Information
    # -----------------------------------------------------------------------#

    def test_read_device_information_request_encode(self):
        """Test basic bit message encoding/decoding"""
        params = {"read_code": DeviceInformation.Basic, "object_id": 0x00}
        handle = ReadDeviceInformationRequest(**params)
        result = handle.encode()
        self.assertEqual(result, b"\x0e\x01\x00")
        self.assertEqual("ReadDeviceInformationRequest(1,0)", str(handle))

    def test_read_device_information_request_decode(self):
        """Test basic bit message encoding/decoding"""
        handle = ReadDeviceInformationRequest()
        handle.decode(b"\x0e\x01\x00")
        self.assertEqual(handle.read_code, DeviceInformation.Basic)
        self.assertEqual(handle.object_id, 0x00)

    def test_read_device_information_request(self):
        """Test basic bit message encoding/decoding"""
        context = None
        control = ModbusControlBlock()
        control.Identity.VendorName = "Company"
        control.Identity.ProductCode = "Product"
        control.Identity.MajorMinorRevision = TEST_VERSION
        control.Identity.update({0x81: ["Test", "Repeated"]})

        handle = ReadDeviceInformationRequest()
        result = handle.execute(context)
        self.assertTrue(isinstance(result, ReadDeviceInformationResponse))
        self.assertEqual(result.information[0x00], "Company")
        self.assertEqual(result.information[0x01], "Product")
        self.assertEqual(result.information[0x02], TEST_VERSION)
        with self.assertRaises(KeyError):
            _ = result.information[0x81]

        handle = ReadDeviceInformationRequest(
            read_code=DeviceInformation.Extended, object_id=0x80
        )
        result = handle.execute(context)
        self.assertEqual(result.information[0x81], ["Test", "Repeated"])

    def test_read_device_information_request_error(self):
        """Test basic bit message encoding/decoding"""
        handle = ReadDeviceInformationRequest()
        handle.read_code = -1
        self.assertEqual(handle.execute(None).function_code, 0xAB)
        handle.read_code = 0x05
        self.assertEqual(handle.execute(None).function_code, 0xAB)
        handle.object_id = -1
        self.assertEqual(handle.execute(None).function_code, 0xAB)
        handle.object_id = 0x100
        self.assertEqual(handle.execute(None).function_code, 0xAB)

    def test_read_device_information_encode(self):
        """Test that the read fifo queue response can encode"""
        message = b"\x0e\x01\x83\x00\x00\x03"
        message += TEST_MESSAGE
        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
        }
        handle = ReadDeviceInformationResponse(
            read_code=DeviceInformation.Basic, information=dataset
        )
        result = handle.encode()
        self.assertEqual(result, message)
        self.assertEqual("ReadDeviceInformationResponse(1)", str(handle))

        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
            0x81: ["Test", "Repeated"],
        }
        message = b"\x0e\x03\x83\x00\x00\x05"
        message += TEST_MESSAGE
        message += b"\x81\x04Test\x81\x08Repeated"
        handle = ReadDeviceInformationResponse(
            read_code=DeviceInformation.Extended, information=dataset
        )
        result = handle.encode()
        self.assertEqual(result, message)

    def test_read_device_information_encode_long(self):
        """Test that the read fifo queue response can encode"""
        longstring = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing "
            "elit. Vivamus rhoncus massa turpis, sit amet ultrices"
            " orci semper ut. Aliquam tristique sapien in lacus "
            "pharetra, in convallis nunc consectetur. Nunc velit "
            "elit, vehicula tempus tempus sed. "
        )

        message = b"\x0e\x01\x83\xFF\x80\x03"
        message += TEST_MESSAGE
        dataset = {
            0x00: "Company",
            0x01: "Product",
            0x02: TEST_VERSION,
            0x80: longstring,
        }
        handle = ReadDeviceInformationResponse(
            read_code=DeviceInformation.Basic, information=dataset
        )
        result = handle.encode()
        self.assertEqual(result, message)
        self.assertEqual("ReadDeviceInformationResponse(1)", str(handle))

    def test_read_device_information_decode(self):
        """Test that the read device information response can decode"""
        message = b"\x0e\x01\x01\x00\x00\x05"
        message += TEST_MESSAGE
        message += b"\x81\x04Test\x81\x08Repeated\x81\x07Another"
        handle = ReadDeviceInformationResponse(read_code=0x00, information=[])
        handle.decode(message)
        self.assertEqual(handle.read_code, DeviceInformation.Basic)
        self.assertEqual(handle.conformity, 0x01)
        self.assertEqual(handle.information[0x00], b"Company")
        self.assertEqual(handle.information[0x01], b"Product")
        self.assertEqual(handle.information[0x02], TEST_VERSION)
        self.assertEqual(handle.information[0x81], [b"Test", b"Repeated", b"Another"])

    def test_rtu_frame_size(self):
        """Test that the read device information response can decode"""
        message = (
            b"\x04\x2B\x0E\x01\x81\x00\x01\x01\x00\x06\x66\x6F\x6F\x62\x61\x72\xD7\x3B"
        )
        result = ReadDeviceInformationResponse.calculateRtuFrameSize(message)
        self.assertEqual(result, 18)
        message = b"\x00\x2B\x0E\x02\x00\x4D\x47"
        result = ReadDeviceInformationRequest.calculateRtuFrameSize(message)
        self.assertEqual(result, 7)
