"""Ascii_framer."""
# pylint: disable=missing-type-doc

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
        self.message_handler = MessageAscii()

    def decode_data(self, data):
        """Decode data."""
        if len(data) > 1:
            uid = int(data[1:3], 16)
            fcode = int(data[3:5], 16)
            return {"slave": uid, "fcode": fcode}
        return {}

    def frameProcessIncomingPacket(self, single, callback, slave, _tid=None, **kwargs):
        """Process new packet pattern."""
        while len(self._buffer):
            used_len, _tid, dev_id, data = self.message_handler.decode(self._buffer)
            if not data:
                if not used_len:
                    return
                self._buffer = self._buffer[used_len :]
                continue
            self._header["uid"] = dev_id
            if not self._validate_slave_id(slave, single):
                Log.error("Not a valid slave id - {}, ignoring!!", dev_id)
                self.resetFrame()
                return

            if (result := self.decoder.decode(data)) is None:
                raise ModbusIOException("Unable to decode response")
            self.populateResult(result)
            self._buffer = self._buffer[used_len :]
            self._header = {"uid": 0x00}
            callback(result)  # defer this

    def buildPacket(self, message):
        """Create a ready to send modbus packet.

        :param message: The request/response to send
        :return: The encoded packet
        """
        data = message.function_code.to_bytes(1,'big') + message.encode()
        packet = self.message_handler.encode(data, message.slave_id, message.transaction_id)
        return packet
