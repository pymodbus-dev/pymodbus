"""Bit Message Test Fixture.

This fixture tests the functionality of all the
bit based request/response messages:

* Read/Write Discretes
* Read Coils
"""

import pymodbus.pdu.bit_message as bit_msg
from pymodbus.pdu import ModbusExceptions

from ..conftest import FakeList, MockContext


res = [True] * 21
res.extend([False] * 3)


class TestModbusBitMessage:
    """Modbus bit read message tests."""

    def test_bit_read_base_response_encoding(self):
        """Test basic bit message encoding/decoding."""
        for i in range(20):
            data = [True] * i
            handle = bit_msg.ReadBitsResponseBase(data, 0, 0, False)
            result = handle.encode()
            handle.decode(result)
            assert handle.bits[:i] == data

    def test_bit_read_base_requests(self):
        """Test bit read request encoding."""
        messages = {
            bit_msg.ReadBitsRequestBase(12, 14, 0, 0, False): b"\x00\x0c\x00\x0e",
            bit_msg.ReadBitsResponseBase([1, 0, 1, 1, 0], 0, 0, False): b"\x01\x0d",
        }
        for request, expected in iter(messages.items()):
            assert request.encode() == expected

    async def test_bit_read_update_datastore_value_errors(self):
        """Test bit read request encoding."""
        context = MockContext()
        requests = [
            bit_msg.ReadCoilsRequest(1, 0x800, 0, 0, False),
            bit_msg.ReadDiscreteInputsRequest(1, 0x800, 0, 0, False),
        ]
        for request in requests:
            result = await request.update_datastore(context)
            assert ModbusExceptions.IllegalValue == result.exception_code

    async def test_bit_read_update_datastore_address_errors(self):
        """Test bit read request encoding."""
        context = MockContext()
        requests = [
            bit_msg.ReadCoilsRequest(1, 5, 0, 0, False),
            bit_msg.ReadDiscreteInputsRequest(1, 5, 0, 0, False),
        ]
        for request in requests:
            result = await request.update_datastore(context)
            assert ModbusExceptions.IllegalAddress == result.exception_code

    async def test_bit_read_update_datastore_success(self):
        """Test bit read request encoding."""
        context = MockContext()
        context.validate = lambda a, b, c: True
        requests = [
            bit_msg.ReadCoilsRequest(1, 5, 0, 0, False),
            bit_msg.ReadDiscreteInputsRequest(1, 5, 0, False),
        ]
        for request in requests:
            result = await request.update_datastore(context)
            assert result.bits == [True] * 5

    def test_bit_read_get_response_pdu(self):
        """Test bit read message get response pdu."""
        requests = {
            bit_msg.ReadCoilsRequest(1, 5, 0, 0, False): 3,
            bit_msg.ReadCoilsRequest(1, 8, 0, 0, False): 3,
            bit_msg.ReadCoilsRequest(0, 16, 0, 0, False): 4,
            bit_msg.ReadDiscreteInputsRequest(1, 21, 0, 0, False): 5,
            bit_msg.ReadDiscreteInputsRequest(1, 24, 0, 0, False): 5,
            bit_msg.ReadDiscreteInputsRequest(1, 1900, 0, 0, False): 240,
        }
        for request, expected in iter(requests.items()):
            pdu_len = request.get_response_pdu_size()
            assert pdu_len == expected

class TestModbusBitWriteMessage:
    """Modbus bit write message tests."""

    def test_bit_write_base_requests(self):
        """Test bit write base."""
        messages = {
            bit_msg.WriteSingleCoilRequest(1, 0xABCD): b"\x00\x01\xff\x00",
            bit_msg.WriteSingleCoilResponse(1, 0xABCD): b"\x00\x01\xff\x00",
            bit_msg.WriteMultipleCoilsRequest(1, [True] * 5): b"\x00\x01\x00\x05\x01\x1f",
            bit_msg.WriteMultipleCoilsResponse(1, 5): b"\x00\x01\x00\x05",
            bit_msg.WriteMultipleCoilsRequest(1, True): b"\x00\x01\x00\x01\x01\x01",
            bit_msg.WriteMultipleCoilsResponse(1, 1): b"\x00\x01\x00\x01",
        }
        for request, expected in iter(messages.items()):
            assert request.encode() == expected

    def test_write_message_get_response_pdu(self):
        """Test bit write message."""
        requests = {bit_msg.WriteSingleCoilRequest(1, 0xABCD): 5}
        for request, expected in iter(requests.items()):
            pdu_len = request.get_response_pdu_size()
            assert pdu_len == expected

    def test_write_multiple_coils_request(self):
        """Test write multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest(1, [True] * 5)
        request.decode(b"\x00\x01\x00\x05\x01\x1f")
        assert request.byte_count == 1
        assert request.address == 1
        assert request.values == [True] * 5
        assert request.get_response_pdu_size() == 5

        request = bit_msg.WriteMultipleCoilsRequest(1, True)
        request.decode(b"\x00\x01\x00\x01\x01\x01")
        assert request.byte_count == 1
        assert request.address == 1
        assert request.values == [True]
        assert request.get_response_pdu_size() == 5

    def test_invalid_write_multiple_coils_request(self):
        """Test write invalid multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest(1, None)
        assert request.values == []

    def test_write_single_coil_request_encode(self):
        """Test write single coil."""
        request = bit_msg.WriteSingleCoilRequest(1, False)
        assert request.encode() == b"\x00\x01\x00\x00"

    async def test_write_single_coil_update_datastore(self):
        """Test write single coil."""
        context = MockContext(False, default=True)
        request = bit_msg.WriteSingleCoilRequest(2, True)
        result = await request.update_datastore(context)
        assert result.exception_code == ModbusExceptions.IllegalAddress

        context.valid = True
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\xff\x00"

        context = MockContext(True, default=False)
        request = bit_msg.WriteSingleCoilRequest(2, False)
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\x00\x00"

    async def test_write_multiple_coils_update_datastore(self):
        """Test write multiple coils."""
        context = MockContext(False)
        # too many values
        request = bit_msg.WriteMultipleCoilsRequest(2, FakeList(0x123456))
        result = await request.update_datastore(context)
        assert result.exception_code == ModbusExceptions.IllegalValue

        # bad byte count
        request = bit_msg.WriteMultipleCoilsRequest(2, [0x00] * 4)
        request.byte_count = 0x00
        result = await request.update_datastore(context)
        assert result.exception_code == ModbusExceptions.IllegalValue

        # does not validate
        context.valid = False
        request = bit_msg.WriteMultipleCoilsRequest(2, [0x00] * 4)
        result = await request.update_datastore(context)
        assert result.exception_code == ModbusExceptions.IllegalAddress

        # validated request
        context.valid = True
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\x00\x04"

    def test_write_multiple_coils_response(self):
        """Test write multiple coils."""
        response = bit_msg.WriteMultipleCoilsResponse()
        response.decode(b"\x00\x80\x00\x08")
        assert response.address == 0x80
        assert response.count == 0x08

    def test_serializing_to_string(self):
        """Test serializing to string."""
        requests = [
            bit_msg.WriteSingleCoilRequest(1, 0xABCD),
            bit_msg.WriteSingleCoilResponse(1, 0xABCD),
            bit_msg.WriteMultipleCoilsRequest(1, [True] * 5),
            bit_msg.WriteMultipleCoilsResponse(1, 5),
        ]
        for request in requests:
            result = str(request)
            assert result

    def test_pass_falsy_value_in_write_multiple_coils_request(self):
        """Test pass falsy value to write multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest(1, 0)
        assert request.values == [0]
