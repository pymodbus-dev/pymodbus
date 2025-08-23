"""Modbus TLS frame implementation."""
from __future__ import annotations

from pymodbus.framer.base import FramerBase


class FramerTLS(FramerBase):
    """Modbus TLS frame type.

    Layout::

        [         MBAP Header         ] [ Function Code] [ Data ]
        [ tid ][ pid ][ length ][ uid ]
          2b     2b     2b        1b           1b           Nb

    length = uid + function code + data
    """

    MIN_SIZE = 8

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode MDAP+payload."""
        tid = int.from_bytes(data[0:2], 'big')
        dev_id = int(data[6])
        return len(data), dev_id, tid, data[7:]

    def encode(self, payload: bytes, device_id: int, tid: int) -> bytes:
        """Encode MDAP+payload."""
        frame = (
           tid.to_bytes(2, 'big') +
           b'\x00\x00' +
           (len(payload) + 1).to_bytes(2, 'big') +
           device_id.to_bytes(1, 'big') +
           payload
        )
        return frame
