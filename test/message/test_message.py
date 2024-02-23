"""Test transport."""

from unittest import mock

import pytest

from pymodbus.message import MessageType
from pymodbus.transport import CommParams


class TestMessage:  # pylint: disable=too-few-public-methods
    """Test message module."""

    @pytest.mark.parametrize(("entry"), list(MessageType))
    async def test_message_init(self, entry, dummy_message):
        """Test message type."""
        dummy_message(entry.value,
            CommParams(),
            False,
            [1],
        )

    async def test_message_callback_data(self, dummy_message):
        """Test message type."""
        msg = dummy_message(MessageType.RAW,
            CommParams(),
            False,
            [1],
        )
        msg.msg_handle.decode = mock.MagicMock(return_value=(5,0,b''))
        assert msg.callback_data(b'') == 5

    async def test_message_callback_data_decode(self, dummy_message):
        """Test message type."""
        msg = dummy_message(MessageType.RAW,
            CommParams(),
            False,
            [1],
        )
        msg.msg_handle.decode = mock.MagicMock(return_value=(17,0,b'decode'))
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

    @pytest.mark.parametrize(("entry"), list(MessageType))
    async def test_message_reset(self, entry, dummy_message):
        """Test message type."""
        msg = dummy_message(entry.value,
            CommParams(),
            False,
            [1],
        )
        msg.msg_handle.reset = mock.Mock()
        msg.reset()
