"""Modbus TLS frame implementation."""
from __future__ import annotations

from pymodbus.framer.base import FramerBase


class FramerTLS(FramerBase):
    """Modbus TLS frame type.

    Layout::
      [ Function Code] [ Data ]
        1b               Nb
    """

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU."""
        return len(data), 0, 0, data

    def encode(self, pdu: bytes, _device_id: int, _tid: int) -> bytes:
        """Encode ADU."""
        return pdu
