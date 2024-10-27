"""Bit Message Test Fixture.

This fixture tests the functionality of all the
bit based request/response messages:

* Read/Write Discretes
* Read Coils
"""

import pymodbus.pdu.bit_message as bit_msg
from pymodbus.pdu import ModbusExceptions

from ..conftest import MockContext


res = [True] * 21
res.extend([False] * 3)


class TestModbusBitMessage:
    """Modbus bit read message tests."""

    def test_bit_read_base_response_encoding(self):
        """Test basic bit message encoding/decoding."""
        for i in range(20):
            data = [True] * i
            pdu =  bit_msg.ReadCoilsResponse()
            pdu.setData(data, 0, 0)
            result = pdu.encode()
            pdu.decode(result)
            assert pdu.bits[:i] == data

    def test_bit_read_base_requests(self):
        """Test bit read request encoding."""
        pdu = bit_msg.ReadCoilsResponse()
        pdu.setData([1, 0, 1, 1, 0], 0, 0)
        messages = {
            bit_msg.ReadCoilsRequest(): b"\x00\x0c\x00\x0e",
            pdu: b"\x01\x0d",
        }
        first = True
        for request, expected in iter(messages.items()):
            if first:
                request.setData(12, 14, 0, 0)
                first = False
            assert request.encode() == expected

    async def test_bit_read_update_datastore_value_errors(self):
        """Test bit read request encoding."""
        context = MockContext()
        pdu1 = bit_msg.ReadCoilsRequest()
        pdu1.setData(1, 0x800, 0, 0)
        pdu2 = bit_msg.ReadDiscreteInputsRequest()
        pdu2.setData(1, 0x800, 0, 0)
        requests = [
            pdu1,
            pdu2,
        ]
        for request in requests:
            result = await request.update_datastore(context)
            assert ModbusExceptions.IllegalValue == result.exception_code

    async def test_bit_read_update_datastore_address_errors(self):
        """Test bit read request encoding."""
        context = MockContext()
        pdu1 = bit_msg.ReadCoilsRequest()
        pdu1.setData(1, 5, 0, 0)
        pdu2 = bit_msg.ReadDiscreteInputsRequest()
        pdu2.setData(1, 5, 0, 0)
        requests = [
            pdu1,
            pdu2,
        ]
        for request in requests:
            result = await request.update_datastore(context)
            assert ModbusExceptions.IllegalAddress == result.exception_code

    async def test_bit_read_update_datastore_success(self):
        """Test bit read request encoding."""
        context = MockContext()
        context.validate = lambda a, b, c: True
        pdu1 = bit_msg.ReadCoilsRequest()
        pdu1.setData(1, 5, 0, 0)
        pdu2 = bit_msg.ReadDiscreteInputsRequest()
        pdu2.setData(1, 5, 0, 0)
        requests = [
            pdu1,
            pdu2,
        ]
        for request in requests:
            result = await request.update_datastore(context)
            assert result.bits == [True] * 5

    def test_bit_read_get_response_pdu(self):
        """Test bit read message get response pdu."""
        pdu1 = bit_msg.ReadCoilsRequest()
        pdu1.setData(1, 5, 0, 0)
        pdu2 = bit_msg.ReadCoilsRequest()
        pdu2.setData(1, 8, 0, 0)
        pdu3 = bit_msg.ReadCoilsRequest()
        pdu3.setData(0, 16, 0, 0)
        pdu4 = bit_msg.ReadDiscreteInputsRequest()
        pdu4.setData(1, 21, 0, 0)
        pdu5 = bit_msg.ReadDiscreteInputsRequest()
        pdu5.setData(1, 24, 0, 0)
        pdu6 = bit_msg.ReadDiscreteInputsRequest()
        pdu6.setData(1, 1900, 0, 0)
        requests = {
            pdu1: 3,
            pdu2: 3,
            pdu3: 4,
            pdu4: 5,
            pdu5: 5,
            pdu6: 240,
        }
        for request, expected in iter(requests.items()):
            pdu_len = request.get_response_pdu_size()
            assert pdu_len == expected

class TestModbusBitWriteMessage:
    """Modbus bit write message tests."""

    def test_bit_write_base_requests(self):
        """Test bit write base."""
        pdu1 = bit_msg.WriteSingleCoilRequest()
        pdu1.setData(1, True, 0, 0)
        pdu2 = bit_msg.WriteSingleCoilResponse()
        pdu2.setData(1, True, 0, 0)
        pdu3 = bit_msg.WriteMultipleCoilsRequest()
        pdu3.setData(1, [True] * 5, 0, 0)
        pdu4 = bit_msg.WriteMultipleCoilsRequest()
        pdu4.setData(1, [True], 0, 0)
        pdu5 = bit_msg.WriteMultipleCoilsResponse()
        pdu5.setData(1, 5, 0, 0)
        pdu6 = bit_msg.WriteMultipleCoilsResponse()
        pdu6.setData(1, 1, 0, 0)
        messages = {
            pdu1: b"\x00\x01\xff\x00",
            pdu2: b"\x00\x01\xff\x00",
            pdu3: b"\x00\x01\x00\x05\x01\x1f",
            pdu5: b"\x00\x01\x00\x05",
            pdu4: b"\x00\x01\x00\x01\x01\x01",
            pdu6: b"\x00\x01\x00\x01",
        }
        for request, expected in iter(messages.items()):
            assert request.encode() == expected

    def test_write_message_get_response_pdu(self):
        """Test bit write message."""
        pdu = bit_msg.WriteSingleCoilRequest()
        pdu.setData(1, True, 0, 0)
        requests = {pdu: 5}
        for request, expected in iter(requests.items()):
            pdu_len = request.get_response_pdu_size()
            assert pdu_len == expected

    def test_write_multiple_coils_request(self):
        """Test write multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest()
        request.setData(1, [True] * 5, 0, 0)
        request.decode(b"\x00\x01\x00\x05\x01\x1f")
        assert request.address == 1
        assert request.values == [True] * 5
        assert request.get_response_pdu_size() == 5

        request = bit_msg.WriteMultipleCoilsRequest()
        request.setData(1, [True], 0, 0)
        request.decode(b"\x00\x01\x00\x01\x01\x01")
        assert request.address == 1
        assert request.values == [True]
        assert request.get_response_pdu_size() == 5

    def test_invalid_write_multiple_coils_request(self):
        """Test write invalid multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest()
        request.setData(1, None, 0, 0)
        assert not request.values

    def test_write_single_coil_request_encode(self):
        """Test write single coil."""
        request = bit_msg.WriteSingleCoilRequest()
        request.setData(1, False, 0, 0)
        assert request.encode() == b"\x00\x01\x00\x00"

    async def test_write_single_coil_update_datastore(self):
        """Test write single coil."""
        context = MockContext(False, default=True)
        request = bit_msg.WriteSingleCoilRequest()
        request.setData(2, True, 0, 0)
        result = await request.update_datastore(context)
        assert result.exception_code == ModbusExceptions.IllegalAddress

        context.valid = True
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\xff\x00"

        context = MockContext(True, default=False)
        request = bit_msg.WriteSingleCoilRequest()
        request.setData(2, False, 0, 0)
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\x00\x00"

    async def test_write_multiple_coils_update_datastore(self):
        """Test write multiple coils."""
        context = MockContext(False)
        # too many values
        request = bit_msg.WriteMultipleCoilsRequest()
        request.setData(2, [], 0, 0)
        result = await request.update_datastore(context)
        assert result.exception_code == ModbusExceptions.IllegalValue

        # does not validate
        context.valid = False
        request = bit_msg.WriteMultipleCoilsRequest()
        request.setData(2, [False] * 4, 0, 0)
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
        pdu1 = bit_msg.WriteSingleCoilRequest()
        pdu1.setData(1, True, 0, 0)
        pdu2 = bit_msg.WriteSingleCoilResponse()
        pdu2.setData(1, True, 0, 0)
        pdu3 = bit_msg.WriteMultipleCoilsRequest()
        pdu3.setData(1, [True] * 5, 0, 0)
        pdu4 = bit_msg.WriteMultipleCoilsResponse()
        pdu4.setData(1, 5, 0, 0)
        requests = [
            pdu1,
            pdu2,
            pdu3,
            pdu4,
        ]
        for request in requests:
            result = str(request)
            assert result

    def test_pass_falsy_value_in_write_multiple_coils_request(self):
        """Test pass falsy value to write multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest()
        request.setData(1, [0], 0, 0)
        assert request.values == [0]
