"""Test transport."""

import pytest

from pymodbus.message import MessageType
from pymodbus.transport import CommParams


class TestMessage:  # pylint: disable=too-few-public-methods
    """Test message module."""

    @pytest.mark.parametrize(("entry"), list(MessageType))
    async def test_message_type(self, entry, dummy_message):
        """Test message type."""
        dummy_message(entry.value,
            CommParams(),
            False,
            [1],
        )
