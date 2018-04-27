import struct
import socket
from binascii import b2a_hex, a2b_hex

from pymodbus.exceptions import ModbusIOException
from pymodbus.utilities import checkLRC, computeLRC
from pymodbus.framer import ModbusFramer, FRAME_HEADER, BYTE_ORDER

# Python 2 compatibility.
try:
    TimeoutError
except NameError:
    TimeoutError = socket.timeout

ASCII_FRAME_HEADER = BYTE_ORDER + FRAME_HEADER

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Modbus ASCII Message
# --------------------------------------------------------------------------- #
class ModbusAsciiFramer(ModbusFramer):
    """
    Modbus ASCII Frame Controller::

        [ Start ][Address ][ Function ][ Data ][ LRC ][ End ]
          1c        2c         2c         Nc     2c      2c

        * data can be 0 - 2x252 chars
        * end is '\\r\\n' (Carriage return line feed), however the line feed
          character can be changed via a special command
        * start is ':'

    This framer is used for serial transmission.  Unlike the RTU protocol,
    the data in this framer is transferred in plain text ascii.
    """

    def __init__(self, decoder, client=None):
        """ Initializes a new instance of the framer

        :param decoder: The decoder implementation to use
        """
        self._buffer = b''
        self._header = {'lrc': '0000', 'len': 0, 'uid': 0x00}
        self._hsize = 0x02
        self._start = b':'
        self._end = b"\r\n"
        self.decoder = decoder
        self.client = client

    # ----------------------------------------------------------------------- #
    # Private Helper Functions
    # ----------------------------------------------------------------------- #
    def decode_data(self, data):
        if len(data) > 1:
            uid = int(data[1:3], 16)
            fcode = int(data[3:5], 16)
            return dict(unit=uid, fcode=fcode)
        return dict()

    def checkFrame(self):
        """ Check and decode the next frame

        :returns: True if we successful, False otherwise
        """
        start = self._buffer.find(self._start)
        if start == -1:
            return False
        if start > 0:  # go ahead and skip old bad data
            self._buffer = self._buffer[start:]
            start = 0

        end = self._buffer.find(self._end)
        if end != -1:
            self._header['len'] = end
            self._header['uid'] = int(self._buffer[1:3], 16)
            self._header['lrc'] = int(self._buffer[end - 2:end], 16)
            data = a2b_hex(self._buffer[start + 1:end - 2])
            return checkLRC(data, self._header['lrc'])
        return False

    def advanceFrame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        self._buffer = self._buffer[self._header['len'] + 2:]
        self._header = {'lrc': '0000', 'len': 0, 'uid': 0x00}

    def isFrameReady(self):
        """ Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        return len(self._buffer) > 1

    def addToFrame(self, message):
        """ Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        """
        self._buffer += message

    def getFrame(self):
        """ Get the next frame from the buffer

        :returns: The frame data or ''
        """
        start = self._hsize + 1
        end = self._header['len'] - 2
        buffer = self._buffer[start:end]
        if end > 0:
            return a2b_hex(buffer)
        return b''

    def resetFrame(self):
        """ Reset the entire message frame.
        This allows us to skip ovver errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        self._buffer = b''
        self._header = {'lrc': '0000', 'len': 0, 'uid': 0x00}

    def populateResult(self, result):
        """ Populates the modbus result header

        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        """
        result.unit_id = self._header['uid']

    # ----------------------------------------------------------------------- #
    # Public Member Functions
    # ----------------------------------------------------------------------- #
    def processIncomingPacket(self, data, callback, unit, **kwargs):
        """
        The new packet processing pattern

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        :param unit: Process if unit id matches, ignore otherwise (could be a
        list of unit ids (server) or single unit id(client/server))
        :param single: True or False (If True, ignore unit address validation)

        """
        if not isinstance(unit, (list, tuple)):
            unit = [unit]
        single = kwargs.get('single', False)
        self.addToFrame(data)
        while self.isFrameReady():
            if self.checkFrame():
                if self._validate_unit_id(unit, single):
                    frame = self.getFrame()
                    result = self.decoder.decode(frame)
                    if result is None:
                        raise ModbusIOException("Unable to decode response")
                    self.populateResult(result)
                    self.advanceFrame()
                    callback(result)  # defer this
                else:
                    _logger.error("Not a valid unit id - {}, "
                                  "ignoring!!".format(self._header['uid']))
                    self.resetFrame()
            else:
                break

    def buildPacket(self, message):
        """ Creates a ready to send modbus packet
        Built off of a  modbus request/response

        :param message: The request/response to send
        :return: The encoded packet
        """
        encoded = message.encode()
        buffer = struct.pack(ASCII_FRAME_HEADER, message.unit_id,
                             message.function_code)
        checksum = computeLRC(encoded + buffer)

        packet = bytearray()
        params = (message.unit_id, message.function_code)
        packet.extend(self._start)
        packet.extend(('%02x%02x' % params).encode())
        packet.extend(b2a_hex(encoded))
        packet.extend(('%02x' % checksum).encode())
        packet.extend(self._end)
        return bytes(packet).upper()


# __END__

