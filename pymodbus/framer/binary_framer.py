"""Binary framer."""
# pylint: disable=missing-type-doc
import struct

from pymodbus.exceptions import ModbusIOException
from pymodbus.framer.base import BYTE_ORDER, FRAME_HEADER, ModbusFramer
from pymodbus.logging import Log
from pymodbus.message.rtu import MessageRTU


BINARY_FRAME_HEADER = BYTE_ORDER + FRAME_HEADER

# --------------------------------------------------------------------------- #
# Modbus Binary Message
# --------------------------------------------------------------------------- #


class ModbusBinaryFramer(ModbusFramer):
    """Modbus Binary Frame Controller.

        [ Start ][Address ][ Function ][ Data ][ CRC ][ End ]
          1b        1b         1b         Nb     2b     1b

        * data can be 0 - 2x252 chars
        * end is   "}"
        * start is "{"

    The idea here is that we implement the RTU protocol, however,
    instead of using timing for message delimiting, we use start
    and end of message characters (in this case { and }). Basically,
    this is a binary framer.

    The only case we have to watch out for is when a message contains
    the { or } characters.  If we encounter these characters, we
    simply duplicate them.  Hopefully we will not encounter those
    characters that often and will save a little bit of bandwitch
    without a real-time system.

    Protocol defined by jamod.sourceforge.net.
    """

    method = "binary"

    def __init__(self, decoder, client=None):
        """Initialize a new instance of the framer.

        :param decoder: The decoder implementation to use
        """
        super().__init__(decoder, client)
        # self._header.update({"crc": 0x0000})
        self._hsize = 0x01
        self._start = b"\x7b"  # {
        self._end = b"\x7d"  # }
        self._repeat = [b"}"[0], b"{"[0]]  # python3 hack

    def decode_data(self, data):
        """Decode data."""
        if len(data) > self._hsize:
            uid = struct.unpack(">B", data[1:2])[0]
            fcode = struct.unpack(">B", data[2:3])[0]
            return {"slave": uid, "fcode": fcode}
        return {}

    def frameProcessIncomingPacket(self, single, callback, slave, _tid=None, **kwargs):
        """Process new packet pattern."""
        def check_frame(self) -> bool:
            """Check and decode the next frame."""
            start = self._buffer.find(self._start)
            if start == -1:
                return False
            if start > 0:  # go ahead and skip old bad data
                self._buffer = self._buffer[start:]

            if (end := self._buffer.find(self._end)) != -1:
                self._header["len"] = end
                self._header["uid"] = struct.unpack(">B", self._buffer[1:2])[0]
                self._header["crc"] = struct.unpack(">H", self._buffer[end - 2 : end])[0]
                data = self._buffer[1 : end - 2]
                return MessageRTU.check_CRC(data, self._header["crc"])
            return False

        while len(self._buffer) > 1:
            if not check_frame(self):
                Log.debug("Frame check failed, ignoring!!")
                break
            if not self._validate_slave_id(slave, single):
                header_txt = self._header["uid"]
                Log.debug("Not a valid slave id - {}, ignoring!!", header_txt)
                self.resetFrame()
                break
            start = self._hsize + 1
            end = self._header["len"] - 2
            buffer = self._buffer[start:end]
            if end > 0:
                frame = buffer
            else:
                frame = b""
            if (result := self.decoder.decode(frame)) is None:
                raise ModbusIOException("Unable to decode response")
            self.populateResult(result)
            self._buffer = self._buffer[self._header["len"] + 2 :]
            self._header = {"crc": 0x0000, "len": 0, "uid": 0x00}
            callback(result)  # defer or push to a thread?

    def buildPacket(self, message):
        """Create a ready to send modbus packet.

        :param message: The request/response to send
        :returns: The encoded packet
        """
        data = self._preflight(message.encode())
        packet = (
            struct.pack(BINARY_FRAME_HEADER, message.slave_id, message.function_code)
            + data
        )
        packet += struct.pack(">H", MessageRTU.compute_CRC(packet))
        packet = self._start + packet + self._end
        return packet

    def _preflight(self, data):
        """Do preflight buffer test.

        This basically scans the buffer for start and end
        tags and if found, escapes them.

        :param data: The message to escape
        :returns: the escaped packet
        """
        array = bytearray()
        for item in data:
            if item in self._repeat:
                array.append(item)
            array.append(item)
        return bytes(array)
