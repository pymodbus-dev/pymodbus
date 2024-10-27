"""Bit Message Test Fixture."""

import pymodbus.pdu.bit_message as bit_msg
from pymodbus.pdu import ModbusExceptions


class TestModbusBitMessage:
    """Modbus bit read message tests."""

    def test_bit_read_base_response_encoding(self):
        """Test basic bit message encoding/decoding."""
        pdu =  bit_msg.ReadCoilsResponse()
        for i in range(1, 20):
            data = [True] * i
            pdu.setData(data, 0, 0)
            pdu.decode(pdu.encode())
            if i % 8:
                data.extend([False] * (8 - (i % 8)))
            assert pdu.bits == data

    def test_bit_read_base_requests(self):
        """Test bit read request encoding."""
        for pdu, args, expected in (
            (bit_msg.ReadCoilsRequest(), (12, 14, 0, 0), b"\x00\x0c\x00\x0e"),
            (bit_msg.ReadCoilsResponse(), ([True, False, True, True, False], 0, 0), b"\x01\x0d"),
        ):
            pdu.setData(*args)
            assert pdu.encode() == expected

    async def test_bit_read_update_datastore_value_errors(self, mock_context):
        """Test bit read request encoding."""
        context = mock_context()
        for pdu, args in (
            (bit_msg.ReadCoilsRequest(), (1, 0x800, 0, 0)),
            (bit_msg.ReadDiscreteInputsRequest(), (1, 0x800, 0, 0)),
        ):
            pdu.setData(*args)
            result = await pdu.update_datastore(context)
            assert ModbusExceptions.IllegalValue == result.exception_code

    async def test_bit_read_update_datastore_address_errors(self, mock_context):
        """Test bit read request encoding."""
        context = mock_context()
        for pdu, args in (
            (bit_msg.ReadCoilsRequest(), (1, 5, 0, 0)),
            (bit_msg.ReadDiscreteInputsRequest(), (1, 5, 0, 0)),
        ):
            pdu.setData(*args)
            result = await pdu.update_datastore(context)
            assert ModbusExceptions.IllegalAddress == result.exception_code

    async def test_bit_read_update_datastore_success(self, mock_context):
        """Test bit read request encoding."""
        context = mock_context()
        context.validate = lambda a, b, c: True
        for pdu, args in (
            (bit_msg.ReadCoilsRequest(), (1, 5, 0, 0)),
            (bit_msg.ReadDiscreteInputsRequest(), (1, 5, 0, 0)),
        ):
            pdu.setData(*args)
            result = await pdu.update_datastore(context)
            assert result.bits == [True] * 5

    def test_bit_read_get_response_pdu(self):
        """Test bit read message get response pdu."""
        for pdu, args, expected in (
            (bit_msg.ReadCoilsRequest(), (1, 5, 0, 0), 3),
            (bit_msg.ReadCoilsRequest(), (1, 8, 0, 0), 3),
            (bit_msg.ReadCoilsRequest(), (1, 16, 0, 0), 4),
            (bit_msg.ReadDiscreteInputsRequest(), (1, 21, 0, 0), 5),
            (bit_msg.ReadDiscreteInputsRequest(), (1, 24, 0, 0), 5),
            (bit_msg.ReadDiscreteInputsRequest(), (1, 1900, 0, 0), 240),
        ):
            pdu.setData(*args)
            assert pdu.get_response_pdu_size() == expected

    def test_bit_write_base_requests(self):
        """Test bit write base."""
        for pdu, args, expected in (
            (bit_msg.WriteSingleCoilRequest(), (1, True, 0, 0), b"\x00\x01\xff\x00"),
            (bit_msg.WriteMultipleCoilsRequest(), (1, [True] * 5, 0, 0), b"\x00\x01\x00\x05\x01\x1f"),
            (bit_msg.WriteMultipleCoilsRequest(), (1, [True], 0, 0), b"\x00\x01\x00\x01\x01\x01"),
            (bit_msg.WriteMultipleCoilsResponse(), (1, 5, 0, 0), b"\x00\x01\x00\x05"),
            (bit_msg.WriteMultipleCoilsResponse(), (1, 1, 0, 0), b"\x00\x01\x00\x01"),
        ):
            pdu.setData(*args)
            assert pdu.encode() == expected

    def test_write_message_get_response_pdu(self):
        """Test bit write message."""
        pdu = bit_msg.WriteSingleCoilRequest()
        pdu.setData(1, True, 0, 0)
        pdu_len = pdu.get_response_pdu_size()
        assert pdu_len == 5

    def test_write_multiple_coils_request(self):
        """Test write multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest()
        for args, frame, values, expected in (
            ((1, [True] * 5, 0, 0), b"\x00\x01\x00\x05\x01\x1f", [True] * 5, 5),
            ((1, [True], 0, 0), b"\x00\x01\x00\x01\x01\x01", [True], 5),
        ):
            request.setData(*args)
            request.decode(frame)
            assert request.address == 1
            assert request.values == values
            assert request.get_response_pdu_size() == expected

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

    async def test_write_single_coil_update_datastore(self, mock_context):
        """Test write single coil."""
        context = mock_context(False, default=True)
        request = bit_msg.WriteSingleCoilRequest()
        request.setData(2, True, 0, 0)
        result = await request.update_datastore(context)
        assert result.exception_code == ModbusExceptions.IllegalAddress

        context.valid = True
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\xff\x00"

        context = mock_context(True, default=False)
        request = bit_msg.WriteSingleCoilRequest()
        request.setData(2, False, 0, 0)
        result = await request.update_datastore(context)
        assert result.encode() == b"\x00\x02\x00\x00"

    async def test_write_multiple_coils_update_datastore(self, mock_context):
        """Test write multiple coils."""
        context = mock_context(False)
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
        for pdu, args in (
            (bit_msg.WriteSingleCoilRequest(), (1, True, 0, 0)),
            (bit_msg.WriteSingleCoilResponse(), (1, True, 0, 0)),
            (bit_msg.WriteMultipleCoilsRequest(), (1, [True] * 5, 0, 0)),
            (bit_msg.WriteMultipleCoilsResponse(), (1, 5, 0, 0)),
        ):
            pdu.setData(*args)
            assert str(pdu)

    def test_pass_falsy_value_in_write_multiple_coils_request(self):
        """Test pass falsy value to write multiple coils."""
        request = bit_msg.WriteMultipleCoilsRequest()
        request.setData(1, [0], 0, 0)
        assert request.values == [0]
