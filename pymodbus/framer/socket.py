"""Modbus Socket frame implementation."""
from __future__ import annotations

from pymodbus.framer.base import FramerBase
from pymodbus.logging import Log


class FramerSocket(FramerBase):
    """Modbus Socket frame type.

    [         MBAP Header         ] [ Function Code] [ Data ]
    [ tid ][ pid ][ length ][ uid ]
      2b     2b     2b        1b           1b           Nb

    * length = uid + function code + data
    """

    MIN_SIZE = 8

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU."""
        if (used_len := len(data)) < self.MIN_SIZE:
          Log.debug("Very short frame (NO MBAP): {} wait for more data", data, ":hex")
          return 0, 0, 0, self.EMPTY
        msg_tid = int.from_bytes(data[0:2], 'big')
        msg_len = int.from_bytes(data[4:6], 'big') + 6
        msg_dev = int(data[6])
        if used_len < msg_len:
          Log.debug("Short frame: {} wait for more data", data, ":hex")
          return 0, 0, 0, self.EMPTY
        if msg_len == 8 and used_len == 9:
            msg_len = 9
        return msg_len, msg_tid, msg_dev, data[7:msg_len]

    def encode(self, pdu: bytes, device_id: int, tid: int) -> bytes:
        """Encode ADU."""
        packet = (
           tid.to_bytes(2, 'big') +
           b'\x00\x00' +
           (len(pdu) + 1).to_bytes(2, 'big') +
           device_id.to_bytes(1, 'big') +
           pdu
        )
        return packet
