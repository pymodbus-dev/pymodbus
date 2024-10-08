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

    def specific_decode(self, data: bytes, data_len: int) -> tuple[int, bytes]:
        """Decode ADU."""
        self.incoming_tid = int.from_bytes(data[0:2], 'big')
        msg_len = int.from_bytes(data[4:6], 'big') + 6
        self.incoming_dev_id = int(data[6])
        if data_len < msg_len:
          Log.debug("Short frame: {} wait for more data", data, ":hex")
          return 0, self.EMPTY
        if msg_len == 8 and data_len == 9:
            msg_len = 9
        return msg_len, data[7:msg_len]

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
