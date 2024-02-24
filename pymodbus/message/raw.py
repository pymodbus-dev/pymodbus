"""ModbusMessage layer."""
from __future__ import annotations

from pymodbus.message.base import MessageBase


class MessageRaw(MessageBase):
    """Raw header.

    HEADER:
        byte[0] = device_id
        byte[1] = transaction_id
        byte[2..] = request/response

    This is mainly for test purposes.
    """

    def reset(self) -> None:
        """Clear internal handling."""

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode message."""
        if len(data) < 3:
            return 0, 0, 0, b''
        return len(data), int(data[0]), int(data[1]), data[2:]

    def encode(self, data: bytes, device_id: int, tid: int) -> bytes:
        """Decode message."""
        return device_id.to_bytes() + tid.to_bytes() + data
