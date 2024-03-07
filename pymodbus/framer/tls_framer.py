"""TLS framer."""
# pylint: disable=missing-type-doc
import struct

from pymodbus.exceptions import (
    ModbusIOException,
)
from pymodbus.framer.base import TLS_FRAME_HEADER, ModbusFramer
from pymodbus.logging import Log
from pymodbus.message.tls import MessageTLS


# --------------------------------------------------------------------------- #
# Modbus TLS Message
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
        self.message_encoder = MessageTLS([0], True)

    def decode_data(self, data):
        """Decode data."""
        if len(data) > self._hsize:
            (fcode,) = struct.unpack(TLS_FRAME_HEADER, data[0 : self._hsize + 1])
            return {"fcode": fcode}
        return {}

    def frameProcessIncomingPacket(self, single, callback, slave, _tid=None, **kwargs):
        """Process new packet pattern."""
        # no slave id for Modbus Security Application Protocol
        def check_frame(self):
            """Check and decode the next frame."""
            if len(self._buffer) > self._hsize:
                # we have at least a complete message, continue
                if len(self._buffer) - self._hsize >= 1:
                    return True
            # we don't have enough of a message yet, wait
            return False

        if not len(self._buffer) > self._hsize:
            return
        if not check_frame(self):
            Log.debug("Frame check failed, ignoring!!")
            self.resetFrame()
            return
        if not self._validate_slave_id(slave, single):
            Log.debug("Not in valid slave id - {}, ignoring!!", slave)
            self.resetFrame()
            return
        data = self._buffer[self._hsize :]
        if (result := self.decoder.decode(data)) is None:
            raise ModbusIOException("Unable to decode request")
        self.populateResult(result)
        self._buffer = b""
        self._header = {}
        callback(result)  # defer or push to a thread?

    def buildPacket(self, message):
        """Create a ready to send modbus packet.

        :param message: The populated request/response to send
        """
        data = message.function_code.to_bytes(1,'big') + message.encode()
        packet = self.message_encoder.encode(data, message.slave_id, message.transaction_id)
        return packet
