import struct
from pymodbus.exceptions import ModbusIOException
from pymodbus.utilities import checkCRC, computeCRC
from pymodbus.framer import ModbusFramer, FRAME_HEADER, BYTE_ORDER

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)

BINARY_FRAME_HEADER = BYTE_ORDER + FRAME_HEADER

# --------------------------------------------------------------------------- #
# Modbus Binary Message
# --------------------------------------------------------------------------- #


class ModbusBinaryFramer(ModbusFramer):
    """
    Modbus Binary Frame Controller::

        [ Start ][Address ][ Function ][ Data ][ CRC ][ End ]
          1b        1b         1b         Nb     2b     1b

        * data can be 0 - 2x252 chars
        * end is   '}'
        * start is '{'

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

    def __init__(self, decoder, client=None):
        """ Initializes a new instance of the framer

        :param decoder: The decoder implementation to use
        """
        self._buffer = b''
        self._header = {'crc': 0x0000, 'len': 0, 'uid': 0x00}
        self._hsize = 0x01
        self._start = b'\x7b'  # {
        self._end = b'\x7d'  # }
        self._repeat = [b'}'[0], b'{'[0]] # python3 hack
        self.decoder = decoder
        self.client = client

    # ----------------------------------------------------------------------- #
    # Private Helper Functions
    # ----------------------------------------------------------------------- #
    def decode_data(self, data):
        if len(data) > self._hsize:
            uid = struct.unpack('>B', data[1:2])[0]
            fcode = struct.unpack('>B', data[2:3])[0]
            return dict(unit=uid, fcode=fcode)
        return dict()

    def checkFrame(self):
        """ Check and decode the next frame

        :returns: True if we are successful, False otherwise
        """
        start = self._buffer.find(self._start)
        if start == -1:
            return False
        if start > 0:  # go ahead and skip old bad data
            self._buffer = self._buffer[start:]

        end = self._buffer.find(self._end)
        if end != -1:
            self._header['len'] = end
            self._header['uid'] = struct.unpack('>B', self._buffer[1:2])[0]
            self._header['crc'] = struct.unpack('>H', self._buffer[end - 2:end])[0]
            data = self._buffer[start + 1:end - 2]
            return checkCRC(data, self._header['crc'])
        return False

    def advanceFrame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        self._buffer = self._buffer[self._header['len'] + 2:]
        self._header = {'crc':0x0000, 'len':0, 'uid':0x00}

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
            return buffer
        return b''

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
        list of unit ids (server) or single unit id(client/server)
        :param single: True or False (If True, ignore unit address validation)

        """
        self.addToFrame(data)
        if not isinstance(unit, (list, tuple)):
            unit = [unit]
        single = kwargs.get('single', False)
        while self.isFrameReady():
            if self.checkFrame():
                if self._validate_unit_id(unit, single):
                    result = self.decoder.decode(self.getFrame())
                    if result is None:
                        raise ModbusIOException("Unable to decode response")
                    self.populateResult(result)
                    self.advanceFrame()
                    callback(result)  # defer or push to a thread?
                else:
                    _logger.debug("Not a valid unit id - {}, "
                                  "ignoring!!".format(self._header['uid']))
                    self.resetFrame()
                    break

            else:
                _logger.debug("Frame check failed, ignoring!!")
                self.resetFrame()
                break

    def buildPacket(self, message):
        """ Creates a ready to send modbus packet

        :param message: The request/response to send
        :returns: The encoded packet
        """
        data = self._preflight(message.encode())
        packet = struct.pack(BINARY_FRAME_HEADER,
                             message.unit_id,
                             message.function_code) + data
        packet += struct.pack(">H", computeCRC(packet))
        packet = self._start + packet + self._end
        return packet

    def _preflight(self, data):
        """
        Preflight buffer test

        This basically scans the buffer for start and end
        tags and if found, escapes them.

        :param data: The message to escape
        :returns: the escaped packet
        """
        array = bytearray()
        for d in data:
            if d in self._repeat:
                array.append(d)
            array.append(d)
        return bytes(array)

    def resetFrame(self):
        """ Reset the entire message frame.
        This allows us to skip ovver errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        self._buffer = b''
        self._header = {'crc': 0x0000, 'len': 0, 'uid': 0x00}


# __END__
