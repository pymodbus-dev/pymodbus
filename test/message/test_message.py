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

    async def test_message_callback_data(self, dummy_message):
        """Test message type."""
        msg = dummy_message(MessageType.RAW,
            CommParams(),
            False,
            [1],
        )
        msg.msg_handle.decode = mock.MagicMock(return_value=(5,0,0,b''))
        assert msg.callback_data(b'') == 5

    async def test_message_callback_data_decode(self, dummy_message):
        """Test message type."""
        msg = dummy_message(MessageType.RAW,
            CommParams(),
            False,
            [1],
        )
        msg.msg_handle.decode = mock.MagicMock(return_value=(17,0,1,b'decode'))
        assert msg.callback_data(b'') == 17

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

    async def test_message_reset(self, dummy_message):
        """Test message type."""
        msg = dummy_message(MessageType.RAW,
            CommParams(),
            False,
            [1],
        )
        msg.msg_handle.reset = mock.Mock()
        msg.reset()

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
