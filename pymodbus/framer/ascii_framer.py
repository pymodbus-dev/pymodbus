"""Ascii_framer."""
# pylint: disable=missing-type-doc
from binascii import a2b_hex

from pymodbus.exceptions import ModbusIOException
from pymodbus.framer.base import BYTE_ORDER, FRAME_HEADER, ModbusFramer
from pymodbus.logging import Log
from pymodbus.message.ascii import MessageAscii


ASCII_FRAME_HEADER = BYTE_ORDER + FRAME_HEADER


# --------------------------------------------------------------------------- #
# Modbus ASCII Message
# --------------------------------------------------------------------------- #
class ModbusAsciiFramer(ModbusFramer):
    r"""Modbus ASCII Frame Controller.

        [ Start ][Address ][ Function ][ Data ][ LRC ][ End ]
          1c        2c         2c         Nc     2c      2c

        * data can be 0 - 2x252 chars
        * end is "\\r\\n" (Carriage return line feed), however the line feed
          character can be changed via a special command
        * start is ":"

    This framer is used for serial transmission.  Unlike the RTU protocol,
    the data in this framer is transferred in plain text ascii.
    """

    method = "ascii"

    def __init__(self, decoder, client=None):
        """Initialize a new instance of the framer.

        :param decoder: The decoder implementation to use
        """
        super().__init__(decoder, client)
        self._hsize = 0x02
        self._start = b":"
        self._end = b"\r\n"
        self.message_handler = MessageAscii([0], True)

    def decode_data(self, data):
        """Decode data."""
        if len(data) > 1:
            uid = int(data[1:3], 16)
            fcode = int(data[3:5], 16)
            return {"slave": uid, "fcode": fcode}
        return {}

    def frameProcessIncomingPacket(self, single, callback, slave, _tid=None, **kwargs):
        """Process new packet pattern."""
        def check_frame(self):
            """Check and decode the next frame."""
            start = self._buffer.find(self._start)
            if start == -1:
                return False
            if start > 0:  # go ahead and skip old bad data
                self._buffer = self._buffer[start:]
                start = 0

            if (end := self._buffer.find(self._end)) != -1:
                self._header["len"] = end
                self._header["uid"] = int(self._buffer[1:3], 16)
                self._header["lrc"] = int(self._buffer[end - 2 : end], 16)
                data = a2b_hex(self._buffer[start + 1 : end - 2])
                return MessageAscii.check_LRC(data, self._header["lrc"])
            return False

        while len(self._buffer) > 1:
            if not check_frame(self):
                break
            if not self._validate_slave_id(slave, single):
                header_txt = self._header["uid"]
                Log.error("Not a valid slave id - {}, ignoring!!", header_txt)
                self.resetFrame()
                continue

            start = self._hsize + 1
            end = self._header["len"] - 2
            buffer = self._buffer[start:end]
            if end > 0:
                frame = a2b_hex(buffer)
            else:
                frame = b""
            if (result := self.decoder.decode(frame)) is None:
                raise ModbusIOException("Unable to decode response")
            self.populateResult(result)
            self._buffer = self._buffer[self._header["len"] + 2 :]
            self._header = {"lrc": "0000", "len": 0, "uid": 0x00}
            callback(result)  # defer this

    def buildPacket(self, message):
        """Create a ready to send modbus packet.

        :param message: The request/response to send
        :return: The encoded packet
        """
        data = message.function_code.to_bytes(1,'big') + message.encode()
        packet = self.message_handler.encode(data, message.slave_id, message.transaction_id)
        return packet
