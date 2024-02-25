"""Test transport."""

from unittest import mock

import pytest

from pymodbus.message import MessageType
from pymodbus.transport import CommParams


class TestMessage:
    """Test message module."""

    @pytest.mark.parametrize(("entry"), list(MessageType))
    async def test_message_init(self, entry, dummy_message):
        """Test message type."""
        msg = dummy_message(entry.value,
            CommParams(),
            False,
            [1],
        )
        assert msg.msg_handle

    @pytest.mark.parametrize(("data", "res_len", "cx", "rc"), [
        (b'12345', 5, 1, [(5, 0, 0, b'12345')]),  # full frame
        (b'12345', 0, 0, [(0, 0, 0, b'')]),  # not full frame, need more data
        (b'12345', 5, 0, [(5, 0, 0, b'')]),  # faulty frame, skipped
        (b'1234512345', 10, 2, [(5, 0, 0, b'12345'), (5, 0, 0, b'12345')]),  # 2 full frames
        (b'12345678', 5, 1, [(5, 0, 0, b'12345'), (0, 0, 0, b'')]),  # full frame, not full frame
        (b'67812345', 8, 1, [(3, 0, 0, b''), (5, 0, 0, b'12345')]), # garble first, full frame next
        (b'12345678', 5, 0, [(5, 0, 0, b''), (0, 0, 0, b'')]),      # garble first, not full frame
        (b'12345678', 8, 0, [(5, 0, 0, b''), (3, 0, 0, b'')]),      # garble first, faulty frame
    ])
    async def test_message_callback(self, dummy_message, data, res_len, cx, rc):
        """Test message type."""
        msg = dummy_message(MessageType.RAW,
            CommParams(),
            False,
            [1],
        )
        msg.callback_request_response = mock.Mock()
        msg.msg_handle.decode = mock.MagicMock(side_effect=iter(rc))
        assert msg.callback_data(data) == res_len
        assert msg.callback_request_response.call_count == cx
        if cx:
            msg.callback_request_response.assert_called_with(b'12345', 0, 0)
        else:
            msg.callback_request_response.assert_not_called()

    async def test_message_build_send(self, dummy_message):
        """Test message type."""
        msg = dummy_message(MessageType.RAW,
            CommParams(),
            False,
            [1],
        )
        msg.msg_handle.encode = mock.MagicMock(return_value=(b'decode'))
        msg.build_send(b'decode', 1, 0)
        msg.msg_handle.encode.assert_called_once()
        msg.send.assert_called_once()

    @pytest.mark.parametrize(
        ("dev_ids", "res"), [
        (None, True),
        ([1], True),
        ([2,3,4], False),
        ])
    async def test_validate_id(self, dummy_message, dev_ids, res):
        """Test message type."""
        msg = dummy_message(MessageType.RAW,
            CommParams(),
            False,
            dev_ids,
        )
        assert res == msg.msg_handle.validate_device_id(1)

    @pytest.mark.parametrize(
        ("msg_type", "data", "res_len", "res_id", "res_tid", "res_data"), [
        (MessageType.RAW, b'\x00\x01', 0, 0, 0, b''),
        (MessageType.RAW, b'\x01\x02\x03', 3, 1, 2, b'\x03'),
        (MessageType.RAW, b'\x04\x05\x06\x07\x08\x09\x00\x01\x02\x03', 10, 4, 5, b'\x06\x07\x08\x09\x00\x01\x02\x03'),
    ])
    async def test_decode(self, dummy_message, msg_type, data, res_id, res_tid, res_len, res_data):
        """Test decode method in all types."""
        msg = dummy_message(msg_type,
            CommParams(),
            False,
            [1],
        )
        t_len, t_id, t_tid, t_data = msg.msg_handle.decode(data)
        assert res_len == t_len
        assert res_id == t_id
        assert res_tid == t_tid
        assert res_data == t_data

    @pytest.mark.parametrize(
        ("msg_type", "data", "dev_id", "tid", "res_data"), [
        (MessageType.RAW, b'\x01\x02', 5, 6, b'\x05\x06\x01\x02'),
        (MessageType.RAW, b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09', 17, 25, b'\x11\x19\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'),
    ])
    async def test_encode(self, dummy_message, msg_type, data, dev_id, tid, res_data):
        """Test decode method in all types."""
        msg = dummy_message(msg_type,
            CommParams(),
            False,
            [1],
        )
        t_data = msg.msg_handle.encode(data, dev_id, tid)
        assert res_data == t_data
