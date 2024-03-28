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
        self.message_handler = MessageTLS()

    def decode_data(self, data):
        """Decode data."""
        if len(data) > self._hsize:
            (fcode,) = struct.unpack(TLS_FRAME_HEADER, data[0 : self._hsize + 1])
            return {"fcode": fcode}
        return {}

    def frameProcessIncomingPacket(self, single, callback, slave, _tid=None, **kwargs):
        """Process new packet pattern."""
        # no slave id for Modbus Security Application Protocol

        while True:
            used_len, use_tid, dev_id, data = self.message_handler.decode(self._buffer)
            if not data:
                if not used_len:
                    return
                self._buffer = self._buffer[used_len :]
                continue
            self._header["uid"] = dev_id
            self._header["tid"] = use_tid
            self._header["pid"] = 0

            if not self._validate_slave_id(slave, single):
                Log.debug("Not in valid slave id - {}, ignoring!!", slave)
                self.resetFrame()
                return
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
        packet = self.message_handler.encode(data, message.slave_id, message.transaction_id)
        return packet
