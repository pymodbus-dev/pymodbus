"""Bit Message Test Fixture.

This fixture tests the functionality of all the
bit based request/response messages:

* Read/Write Discretes
* Read Coils
"""
import struct
from test.conftest import MockContext

from pymodbus.bit_read_message import (
    ReadBitsRequestBase,
    ReadBitsResponseBase,
    ReadCoilsRequest,
    ReadDiscreteInputsRequest,
)
from pymodbus.pdu import ModbusExceptions


res = [True] * 21
res.extend([False] * 3)
# ---------------------------------------------------------------------------#
#  Fixture
# ---------------------------------------------------------------------------#


class TestModbusBitMessage:
    """Modbus bit read message tests."""

    # -----------------------------------------------------------------------#
    #  Setup/TearDown
    # -----------------------------------------------------------------------#

    def setUp(self):
        """Initialize the test environment and builds request/result encoding pairs."""

    def tearDown(self):
        """Clean up the test environment"""

    def test_read_bit_base_class_methods(self):
        """Test basic bit message encoding/decoding"""
        handle = ReadBitsRequestBase(1, 1)
        msg = "ReadBitRequest(1,1)"
        assert msg == str(handle)
        handle = ReadBitsResponseBase([1, 1])
        msg = "ReadBitsResponseBase(2)"
        assert msg == str(handle)

    def test_bit_read_base_request_encoding(self):
        """Test basic bit message encoding/decoding"""
        for i in range(20):
            handle = ReadBitsRequestBase(i, i)
            result = struct.pack(">HH", i, i)
            assert handle.encode() == result
            handle.decode(result)
            assert (handle.address, handle.count) == (i, i)

    def test_bit_read_base_response_encoding(self):
        """Test basic bit message encoding/decoding"""
        for i in range(20):
            data = [True] * i
            handle = ReadBitsResponseBase(data)
            result = handle.encode()
            handle.decode(result)
            assert handle.bits[:i] == data

    def test_bit_read_base_response_helper_methods(self):
        """Test the extra methods on a ReadBitsResponseBase"""
        data = [False] * 8
        handle = ReadBitsResponseBase(data)
        for i in (1, 3, 5):
            handle.setBit(i, True)
        for i in (1, 3, 5):
            handle.resetBit(i)
        for i in range(8):
            assert not handle.getBit(i)

    def test_bit_read_base_requests(self):
        """Test bit read request encoding"""
        messages = {
            ReadBitsRequestBase(12, 14): b"\x00\x0c\x00\x0e",
            ReadBitsResponseBase([1, 0, 1, 1, 0]): b"\x01\x0d",
        }
        for request, expected in iter(messages.items()):
            assert request.encode() == expected

    def test_bit_read_message_execute_value_errors(self):
        """Test bit read request encoding"""
        context = MockContext()
        requests = [
            ReadCoilsRequest(1, 0x800),
            ReadDiscreteInputsRequest(1, 0x800),
        ]
        for request in requests:
            result = request.execute(context)
            assert ModbusExceptions.IllegalValue == result.exception_code

    def test_bit_read_message_execute_address_errors(self):
        """Test bit read request encoding"""
        context = MockContext()
        requests = [
            ReadCoilsRequest(1, 5),
            ReadDiscreteInputsRequest(1, 5),
        ]
        for request in requests:
            result = request.execute(context)
            assert ModbusExceptions.IllegalAddress == result.exception_code

    def test_bit_read_message_execute_success(self):
        """Test bit read request encoding"""
        context = MockContext()
        context.validate = lambda a, b, c: True
        requests = [
            ReadCoilsRequest(1, 5),
            ReadDiscreteInputsRequest(1, 5),
        ]
        for request in requests:
            result = request.execute(context)
            assert result.bits == [True] * 5

    def test_bit_read_message_get_response_pdu(self):
        """Test bit read message get response pdu."""
        requests = {
            ReadCoilsRequest(1, 5): 3,
            ReadCoilsRequest(1, 8): 3,
            ReadCoilsRequest(0, 16): 4,
            ReadDiscreteInputsRequest(1, 21): 5,
            ReadDiscreteInputsRequest(1, 24): 5,
            ReadDiscreteInputsRequest(1, 1900): 240,
        }
        for request, expected in iter(requests.items()):
            pdu_len = request.get_response_pdu_size()
            assert pdu_len == expected
