"""TLS framer."""
import struct

from pymodbus.exceptions import (
    ModbusIOException,
)
from pymodbus.framer.old_framer_base import TLS_FRAME_HEADER, ModbusFramer
from pymodbus.framer.tls import FramerTLS


# --------------------------------------------------------------------------- #
# Modbus TLS old framer
# --------------------------------------------------------------------------- #


class ModbusTlsFramer(ModbusFramer):
    """Modbus TLS Frame controller.

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
        self.message_handler = FramerTLS()

    def decode_data(self, data):
        """Decode data."""
        if len(data) > self._hsize:
            (fcode,) = struct.unpack(TLS_FRAME_HEADER, data[0 : self._hsize + 1])
            return {"fcode": fcode}
        return {}

    def frameProcessIncomingPacket(self, _single, callback, _slave, tid=None):
        """Process new packet pattern."""
        # no slave id for Modbus Security Application Protocol

        while True:
            used_len, use_tid, dev_id, data = self.message_handler.decode(self._buffer)
            if not data:
                return
            self.dev_id = dev_id
            self.tid = use_tid

            if (result := self.decoder.decode(data)) is None:
                self.resetFrame()
                raise ModbusIOException("Unable to decode request")
            self.populateResult(result)
            self._buffer: bytes = self._buffer[used_len:]
            callback(result)  # defer or push to a thread?
