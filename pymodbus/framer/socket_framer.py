import struct
from pymodbus.exceptions import ModbusIOException
from pymodbus.exceptions import InvalidMessageReceivedException
from pymodbus.utilities import hexlify_packets
from pymodbus.framer import ModbusFramer, SOCKET_FRAME_HEADER

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
import logging
_logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Modbus TCP Message
# --------------------------------------------------------------------------- #


class ModbusSocketFramer(ModbusFramer):
    """ Modbus Socket Frame controller

    Before each modbus TCP message is an MBAP header which is used as a
    message frame.  It allows us to easily separate messages as follows::

        [         MBAP Header         ] [ Function Code] [ Data ]
        [ tid ][ pid ][ length ][ uid ]
          2b     2b     2b        1b           1b           Nb

        while len(message) > 0:
            tid, pid, length`, uid = struct.unpack(">HHHB", message)
            request = message[0:7 + length - 1`]
            message = [7 + length - 1:]

        * length = uid + function code + data
        * The -1 is to account for the uid byte
    """

    def __init__(self, decoder, client=None):
        """ Initializes a new instance of the framer

        :param decoder: The decoder factory implementation to use
        """
        self._buffer = b''
        self._header = {'tid': 0, 'pid': 0, 'len': 0, 'uid': 0}
        self._hsize = 0x07
        self.decoder = decoder
        self.client = client

    # ----------------------------------------------------------------------- #
    # Private Helper Functions
    # ----------------------------------------------------------------------- #
    def checkFrame(self):
        """
        Check and decode the next frame Return true if we were successful
        """
        if self.isFrameReady():
            (self._header['tid'], self._header['pid'],
             self._header['len'], self._header['uid']) = struct.unpack(
                '>HHHB', self._buffer[0:self._hsize])

            # someone sent us an error? ignore it
            if self._header['len'] < 2:
                self.advanceFrame()
            # we have at least a complete message, continue
            elif len(self._buffer) - self._hsize + 1 >= self._header['len']:
                return True
        # we don't have enough of a message yet, wait
        return False

    def advanceFrame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        length = self._hsize + self._header['len'] - 1
        self._buffer = self._buffer[length:]
        self._header = {'tid': 0, 'pid': 0, 'len': 0, 'uid': 0}

    def isFrameReady(self):
        """ Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder factory know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        return len(self._buffer) > self._hsize

    def addToFrame(self, message):
        """ Adds new packet data to the current frame buffer

        :param message: The most recent packet
        """
        self._buffer += message

    def getFrame(self):
        """ Return the next frame from the buffered data

        :returns: The next full frame buffer
        """
        length = self._hsize + self._header['len'] - 1
        return self._buffer[self._hsize:length]

    def populateResult(self, result):
        """
        Populates the modbus result with the transport specific header
        information (pid, tid, uid, checksum, etc)

        :param result: The response packet
        """
        result.transaction_id = self._header['tid']
        result.protocol_id = self._header['pid']
        result.unit_id = self._header['uid']

    # ----------------------------------------------------------------------- #
    # Public Member Functions
    # ----------------------------------------------------------------------- #
    def decode_data(self, data):
        if len(data) > self._hsize:
            tid, pid, length, uid, fcode = struct.unpack(SOCKET_FRAME_HEADER,
                                                         data[0:self._hsize+1])
            return dict(tid=tid, pid=pid, lenght=length, unit=uid, fcode=fcode)
        return dict()

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
        if not isinstance(unit, (list, tuple)):
            unit = [unit]
        single = kwargs.get("single", False)
        _logger.debug("Processing: " + hexlify_packets(data))
        self.addToFrame(data)
        while True:
            if self.isFrameReady():
                if self.checkFrame():
                    if self._validate_unit_id(unit, single):
                        self._process(callback)
                    else:
                        _logger.debug("Not a valid unit id - {}, "
                                      "ignoring!!".format(self._header['uid']))
                        self.resetFrame()
                else:
                    _logger.debug("Frame check failed, ignoring!!")
                    self.resetFrame()
            else:
                if len(self._buffer):
                    # Possible error ???
                    if self._header['len'] < 2:
                        self._process(callback, error=True)
                break

    def _process(self, callback, error=False):
        """
        Process incoming packets irrespective error condition
        """
        data = self.getRawFrame() if error else self.getFrame()
        result = self.decoder.decode(data)
        if result is None:
            raise ModbusIOException("Unable to decode request")
        elif error and result.function_code < 0x80:
            raise InvalidMessageReceivedException(result)
        else:
            self.populateResult(result)
            self.advanceFrame()
            callback(result)  # defer or push to a thread?

    def resetFrame(self):
        """
        Reset the entire message frame.
        This allows us to skip ovver errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        self._buffer = b''
        self._header = {'tid': 0, 'pid': 0, 'len': 0, 'uid': 0}

    def getRawFrame(self):
        """
        Returns the complete buffer
        """
        return self._buffer

    def buildPacket(self, message):
        """ Creates a ready to send modbus packet

        :param message: The populated request/response to send
        """
        data = message.encode()
        packet = struct.pack(SOCKET_FRAME_HEADER,
                             message.transaction_id,
                             message.protocol_id,
                             len(data) + 2,
                             message.unit_id,
                             message.function_code)
        packet += data
        return packet


# __END__
