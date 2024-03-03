"""ModbusMessage layer.

is extending ModbusProtocol to handle receiving and sending of messsagees.

ModbusMessage provides a unified interface to send/receive Modbus requests/responses.
"""
from __future__ import annotations

from pymodbus.message.base import MessageBase


class MessageTLS(MessageBase):
    """Modbus TLS frame type.

    [ Function Code] [ Data ]
      1b               Nb
    """

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode message."""
        return len(data), 0, 0, data

    def encode(self, data: bytes, _device_id: int, _tid: int) -> bytes:
        """Decode message."""
        return data
