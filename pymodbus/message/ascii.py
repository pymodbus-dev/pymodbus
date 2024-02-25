"""ModbusMessage layer.

is extending ModbusProtocol to handle receiving and sending of messsagees.

ModbusMessage provides a unified interface to send/receive Modbus requests/responses.
"""
from __future__ import annotations

from binascii import a2b_hex, b2a_hex

from pymodbus.logging import Log
from pymodbus.message.base import MessageBase


class MessageAscii(MessageBase):
    r"""Modbus ASCII Frame Controller.

        [ Start ][Address ][ Function ][ Data ][ LRC ][ End ]
          1c        2c         2c         Nc     1c      2c

        * data can be 0 - 2x252 chars
        * end is "\\r\\n" (Carriage return line feed), however the line feed
          character can be changed via a special command
        * start is ":"

    This framer is used for serial transmission.  Unlike the RTU protocol,
    the data in this framer is transferred in plain text ascii.
    """

    START = b':'
    END = b'\r\n'


    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode message."""
        if (used_len := len(data)) < 10:
            Log.debug("Short frame: {} wait for more data", data, ":hex")
            return 0, 0, 0, self.EMPTY
        if data[0:1] != self.START:
            if (start := data.find(self.START)) != -1:
                used_len = start
            Log.debug("Garble data before frame: {}, skip until start of frame", data, ":hex")
            return used_len, 0, 0, self.EMPTY
        if (used_len := data.find(self.END)) == -1:
            Log.debug("Incomplete frame: {} wait for more data", data, ":hex")
            return 0, 0, 0, self.EMPTY

        dev_id = int(data[1:3], 16)
        lrc = int(data[used_len - 2: used_len], 16)
        msg = a2b_hex(data[1 : used_len - 2])
        if not self.check_LRC(msg, lrc):
            Log.debug("LRC wrong in frame: {} skipping", data, ":hex")
            return used_len+2, 0, 0, self.EMPTY
        return used_len+2, 0, dev_id, msg[1:]

    def encode(self, data: bytes, device_id: int, _tid: int) -> bytes:
        """Decode message."""
        dev_id = device_id.to_bytes(1,'big')
        checksum = self.compute_LRC(dev_id + data)
        packet = (
            self.START +
            f"{device_id:02x}".encode() +
            b2a_hex(data) +
            f"{checksum:02x}".encode() +
            self.END
        ).upper()
        return packet

    @classmethod
    def compute_LRC(cls, data: bytes) -> int:
        """Use to compute the longitudinal redundancy check against a string."""
        lrc = sum(int(a) for a in data) & 0xFF
        lrc = (lrc ^ 0xFF) + 1
        return lrc & 0xFF

    @classmethod
    def check_LRC(cls, data: bytes, check: int) -> bool:
        """Check if the passed in data matches the LRC."""
        return cls.compute_LRC(data) == check
