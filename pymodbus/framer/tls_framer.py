"""TLS framer."""
# pylint: disable=missing-type-doc
import struct

from pymodbus.exceptions import (
    InvalidMessageReceivedException,
    ModbusIOException,
)
from pymodbus.framer.base import TLS_FRAME_HEADER, ModbusFramer
from pymodbus.logging import Log


# --------------------------------------------------------------------------- #
# Modbus TLS Message
# --------------------------------------------------------------------------- #


class ModbusTlsFramer(ModbusFramer):
    """Modbus TLS Frame controller

    No prefix MBAP header before decrypted PDU is used as a message frame for
    Modbus Security Application Protocol.  It allows us to easily separate
    decrypted messages which is PDU as follows:

        [ Function Code] [ Data ]
          1b               Nb
    """

    method = "tls"

    def __init__(self, decoder, client=None):
        """Initialize a new instance of the framer.

        :param decoder: The decoder factory implementation to use
        """
        super().__init__(decoder, client)
        self._hsize = 0x0

    # ----------------------------------------------------------------------- #
    # Private Helper Functions
    # ----------------------------------------------------------------------- #
    def checkFrame(self):
        """Check and decode the next frame.

        Return true if we were successful.
        """
        if self.isFrameReady():
            # we have at least a complete message, continue
            if len(self._buffer) - self._hsize >= 1:
                return True
        # we don't have enough of a message yet, wait
        return False

    def advanceFrame(self):
        """Skip over the current framed message.

        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        self._buffer = b""
        self._header = {}

    def isFrameReady(self):
        """Check if we should continue decode logic.

        This is meant to be used in a while loop in the decoding phase to let
        the decoder factory know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        return len(self._buffer) > self._hsize

    def getFrame(self):
        """Return the next frame from the buffered data.

        :returns: The next full frame buffer
        """
        return self._buffer[self._hsize :]

    # ----------------------------------------------------------------------- #
    # Public Member Functions
    # ----------------------------------------------------------------------- #
    def decode_data(self, data):
        """Decode data."""
        if len(data) > self._hsize:
            (fcode,) = struct.unpack(TLS_FRAME_HEADER, data[0 : self._hsize + 1])
            return {"fcode": fcode}
        return {}

    def frameProcessIncomingPacket(self, single, callback, slave, _tid=None, **kwargs):
        """Process new packet pattern."""
        # no slave id for Modbus Security Application Protocol
        if not self.isFrameReady():
            return
        if not self.checkFrame():
            Log.debug("Frame check failed, ignoring!!")
            self.resetFrame()
            return
        if not self._validate_slave_id(slave, single):
            Log.debug("Not in valid slave id - {}, ignoring!!", slave)
            self.resetFrame()
        self._process(callback)

    def _process(self, callback, error=False):
        """Process incoming packets irrespective error condition."""
        data = self._buffer if error else self.getFrame()
        if (result := self.decoder.decode(data)) is None:
            raise ModbusIOException("Unable to decode request")
        if error and result.function_code < 0x80:
            raise InvalidMessageReceivedException(result)
        self.populateResult(result)
        self.advanceFrame()
        callback(result)  # defer or push to a thread?

    def buildPacket(self, message):
        """Create a ready to send modbus packet.

        :param message: The populated request/response to send
        """
        data = message.encode()
        packet = struct.pack(TLS_FRAME_HEADER, message.function_code)
        packet += data
        return packet


# __END__
