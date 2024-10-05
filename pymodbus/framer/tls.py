"""Modbus TLS frame implementation."""
from __future__ import annotations

from pymodbus.framer.base import FramerBase


class FramerTLS(FramerBase):
    """Modbus TLS frame type.

    [ Function Code] [ Data ]
      1b               Nb
    """

    def specific_decode(self, data: bytes, data_len: int) -> tuple[int, bytes]:
        """Decode ADU."""
        return data_len, data

    def encode(self, pdu: bytes, _device_id: int, _tid: int) -> bytes:
        """Encode ADU."""
        return pdu
