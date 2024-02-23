"""ModbusMessage layer."""
from __future__ import annotations

from pymodbus.message.base import MessageBase


class MessageRaw(MessageBase):
    """Raw header.

    HEADER:
        byte[0] = device_id
        byte[1-2] = length of request/response, NOT converted
        byte[3..] = request/response

    This is mainly for test purposes.
    """

    def reset(self) -> None:
        """Clear internal handling."""

    def decode(self, _data: bytes) -> tuple[int, int, bytes]:
        """Decode message."""
        return 0, 0, b''

    def encode(self, data: bytes, device_id: int, tid: int) -> bytes:
        """Decode message."""
        return b''
