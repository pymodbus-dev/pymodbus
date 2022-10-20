"""Bit Message Test Fixture.

This fixture tests the functionality of all the
bit based request/response messages:

* Read/Write Discretes
* Read Coils
"""
import unittest
from test.conftest import FakeList, MockContext

from pymodbus.bit_write_message import (
    WriteMultipleCoilsRequest,
    WriteMultipleCoilsResponse,
    WriteSingleCoilRequest,
    WriteSingleCoilResponse,
)
from pymodbus.pdu import ModbusExceptions


# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class ModbusBitMessageTests(unittest.TestCase):
    """Modbus bit write message tests."""

    # -----------------------------------------------------------------------#
    #  Setup/TearDown
    # -----------------------------------------------------------------------#

    def setUp(self):
        """Initialize the test environment and builds request/result encoding pairs."""

    def tearDown(self):
        """Clean up the test environment"""

    def test_bit_write_base_requests(self):
        """Test bit write base."""
        messages = {
            WriteSingleCoilRequest(1, 0xABCD): b"\x00\x01\xff\x00",
            WriteSingleCoilResponse(1, 0xABCD): b"\x00\x01\xff\x00",
            WriteMultipleCoilsRequest(1, [True] * 5): b"\x00\x01\x00\x05\x01\x1f",
            WriteMultipleCoilsResponse(1, 5): b"\x00\x01\x00\x05",
        }
        for request, expected in iter(messages.items()):
            self.assertEqual(request.encode(), expected)

    def test_bit_write_message_get_response_pdu(self):
        """Test bit write message."""
        requests = {WriteSingleCoilRequest(1, 0xABCD): 5}
        for request, expected in iter(requests.items()):
            pdu_len = request.get_response_pdu_size()
            self.assertEqual(pdu_len, expected)

    def test_write_multiple_coils_request(self):
        """Test write multiple coils."""
        request = WriteMultipleCoilsRequest(1, [True] * 5)
        request.decode(b"\x00\x01\x00\x05\x01\x1f")
        self.assertEqual(request.byte_count, 1)
        self.assertEqual(request.address, 1)
        self.assertEqual(request.values, [True] * 5)
        self.assertEqual(request.get_response_pdu_size(), 5)

    def test_invalid_write_multiple_coils_request(self):
        """Test write invalid multiple coils."""
        request = WriteMultipleCoilsRequest(1, None)
        self.assertEqual(request.values, [])

    def test_write_single_coil_request_encode(self):
        """Test write single coil."""
        request = WriteSingleCoilRequest(1, False)
        self.assertEqual(request.encode(), b"\x00\x01\x00\x00")

    def test_write_single_coil_execute(self):
        """Test write single coil."""
        context = MockContext(False, default=True)
        request = WriteSingleCoilRequest(2, True)
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalAddress)

        context.valid = True
        result = request.execute(context)
        self.assertEqual(result.encode(), b"\x00\x02\xff\x00")

        context = MockContext(True, default=False)
        request = WriteSingleCoilRequest(2, False)
        result = request.execute(context)
        self.assertEqual(result.encode(), b"\x00\x02\x00\x00")

    def test_write_multiple_coils_execute(self):
        """Test write multiple coils."""
        context = MockContext(False)
        # too many values
        request = WriteMultipleCoilsRequest(2, FakeList(0x123456))
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        # bad byte count
        request = WriteMultipleCoilsRequest(2, [0x00] * 4)
        request.byte_count = 0x00
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalValue)

        # does not validate
        context.valid = False
        request = WriteMultipleCoilsRequest(2, [0x00] * 4)
        result = request.execute(context)
        self.assertEqual(result.exception_code, ModbusExceptions.IllegalAddress)

        # validated request
        context.valid = True
        result = request.execute(context)
        self.assertEqual(result.encode(), b"\x00\x02\x00\x04")

    def test_write_multiple_coils_response(self):
        """Test write multiple coils."""
        response = WriteMultipleCoilsResponse()
        response.decode(b"\x00\x80\x00\x08")
        self.assertEqual(response.address, 0x80)
        self.assertEqual(response.count, 0x08)

    def test_serializing_to_string(self):
        """Test serializing to string."""
        requests = [
            WriteSingleCoilRequest(1, 0xABCD),
            WriteSingleCoilResponse(1, 0xABCD),
            WriteMultipleCoilsRequest(1, [True] * 5),
            WriteMultipleCoilsResponse(1, 5),
        ]
        for request in requests:
            result = str(request)
            self.assertTrue(result is not None and len(result))
