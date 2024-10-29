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
        """Decode MDAP+PDU."""
        tid = int.from_bytes(data[0:2], 'big')
        dev_id = int(data[6])
        return len(data), dev_id, tid, data[7:]

    def encode(self, pdu: bytes, device_id: int, tid: int) -> bytes:
        """Encode MDAP+PDU."""
        frame = (
           tid.to_bytes(2, 'big') +
           b'\x00\x00' +
           (len(pdu) + 1).to_bytes(2, 'big') +
           device_id.to_bytes(1, 'big') +
           pdu
        )
        return frame
