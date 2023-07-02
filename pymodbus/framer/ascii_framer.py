"""Ascii_framer."""
# pylint: disable=missing-type-doc
import struct
from binascii import a2b_hex, b2a_hex

from pymodbus.exceptions import ModbusIOException
from pymodbus.framer.base import BYTE_ORDER, FRAME_HEADER, ModbusFramer
from pymodbus.logging import Log
from pymodbus.utilities import checkLRC, computeLRC


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

    # ----------------------------------------------------------------------- #
    # Private Helper Functions
    # ----------------------------------------------------------------------- #
    def decode_data(self, data):
        """Decode data."""
        if len(data) > 1:
            uid = int(data[1:3], 16)
            fcode = int(data[3:5], 16)
            return {"slave": uid, "fcode": fcode}
        return {}

    def checkFrame(self):
        """Check and decode the next frame.

        :returns: True if we successful, False otherwise
        """
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
            return checkLRC(data, self._header["lrc"])
        return False

    def advanceFrame(self):
        """Skip over the current framed message.

        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        self._buffer = self._buffer[self._header["len"] + 2 :]
        self._header = {"lrc": "0000", "len": 0, "uid": 0x00}

    def isFrameReady(self):
        """Check if we should continue decode logic.

        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        return len(self._buffer) > 1

    def getFrame(self):
        """Get the next frame from the buffer.

        :returns: The frame data or ""
        """
        start = self._hsize + 1
        end = self._header["len"] - 2
        buffer = self._buffer[start:end]
        if end > 0:
            return a2b_hex(buffer)
        return b""

    # ----------------------------------------------------------------------- #
    # Public Member Functions
    # ----------------------------------------------------------------------- #
    def frameProcessIncomingPacket(self, single, callback, slave, _tid=None, **kwargs):
        """Process new packet pattern."""
        while self.isFrameReady():
            if not self.checkFrame():
                break
            if not self._validate_slave_id(slave, single):
                header_txt = self._header["uid"]
                Log.error("Not a valid slave id - {}, ignoring!!", header_txt)
                self.resetFrame()
                continue

            frame = self.getFrame()
            if (result := self.decoder.decode(frame)) is None:
                raise ModbusIOException("Unable to decode response")
            self.populateResult(result)
            self.advanceFrame()
            callback(result)  # defer this

    def buildPacket(self, message):
        """Create a ready to send modbus packet.

        Built off of a  modbus request/response

        :param message: The request/response to send
        :return: The encoded packet
        """
        encoded = message.encode()
        buffer = struct.pack(
            ASCII_FRAME_HEADER, message.slave_id, message.function_code
        )
        checksum = computeLRC(encoded + buffer)

        packet = bytearray()
        packet.extend(self._start)
        packet.extend(f"{message.slave_id:02x}{message.function_code:02x}".encode())
        packet.extend(b2a_hex(encoded))
        packet.extend(f"{checksum:02x}".encode())
        packet.extend(self._end)
        return bytes(packet).upper()


# __END__
