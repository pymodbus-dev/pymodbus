"""ModbusMessage layer.

is extending ModbusProtocol to handle receiving and sending of messsagees.

ModbusMessage provides a unified interface to send/receive Modbus requests/responses.
"""
from __future__ import annotations

from pymodbus.logging import Log
from pymodbus.message.base import MessageBase


class MessageSocket(MessageBase):
    """Modbus Socket frame type.

    [         MBAP Header         ] [ Function Code] [ Data ]
    [ tid ][ pid ][ length ][ uid ]
      2b     2b     2b        1b           1b           Nb

    * length = uid + function code + data
    """

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode message."""
        if (used_len := len(data)) < 9:
          Log.debug("Very short frame (NO MBAP): {} wait for more data", data, ":hex")
          return 0, 0, 0, self.EMPTY
        msg_tid = int.from_bytes(data[0:2], 'big')
        msg_len = int.from_bytes(data[4:6], 'big') + 6
        msg_dev = int(data[6])
        if used_len < msg_len:
          Log.debug("Short frame: {} wait for more data", data, ":hex")
          return 0, 0, 0, self.EMPTY
        return msg_len, msg_tid, msg_dev, data[7:msg_len]

    def encode(self, data: bytes, device_id: int, tid: int) -> bytes:
        """Decode message."""
        packet = (
           tid.to_bytes(2, 'big') +
           b'\x00\x00' +
           (len(data) + 1).to_bytes(2, 'big') +
           device_id.to_bytes(1, 'big') +
           data
        )
        return packet
