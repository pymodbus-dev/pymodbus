"""Framer start."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer.base import FramerBase
from pymodbus.logging import Log
from pymodbus.pdu import ModbusRequest, ModbusResponse


if TYPE_CHECKING:
    pass

# Unit ID, Function Code
BYTE_ORDER = ">"
FRAME_HEADER = "BB"

# Transaction Id, Protocol ID, Length, Unit ID, Function Code
SOCKET_FRAME_HEADER = BYTE_ORDER + "HHH" + FRAME_HEADER

# Function Code
TLS_FRAME_HEADER = BYTE_ORDER + "B"


class ModbusFramer:
    """Base Framer class."""

    def __init__(
        self,
        decoder: ClientDecoder | ServerDecoder,
        _client,
        new_framer,
    ) -> None:
        """Initialize a new instance of the framer.

        :param decoder: The decoder implementation to use
        """
        self.message_handler: FramerBase = new_framer(decoder, [0])

    @property
    def dev_id(self) -> int:
        """Return dev id."""
        return self.message_handler.incoming_dev_id

    @property
    def incoming_dev_id(self) -> int:
        """Return dev id."""
        return self.message_handler.incoming_dev_id

    @property
    def incoming_tid(self) -> int:
        """Return tid."""
        return self.message_handler.incoming_tid

    @property
    def tid(self) -> int:
        """Return tid."""
        return self.message_handler.incoming_tid

    def processIncomingPacket(self, data: bytes, callback, slave, tid=None):
        """Process new packet pattern.

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 // N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.
        """
        Log.debug("Processing: {}", data, ":hex")
        self.message_handler.databuffer += data
        if self.message_handler.databuffer == b'':
            return
        if not isinstance(slave, (list, tuple)):
            slave = [slave]
        while True:
            if self.message_handler.databuffer == b'':
                return
            used_len, data = self.message_handler.decode(self.message_handler.databuffer)
            if used_len:
                self.message_handler.databuffer = self.message_handler.databuffer[used_len:]
            if not data:
                return
            if slave and 0 not in slave and self.message_handler.incoming_dev_id not in slave:
                Log.debug("Not a valid slave id - {}, ignoring!!", self.message_handler.incoming_dev_id)
                self.message_handler.databuffer = b''
                continue
            if (result := self.message_handler.decoder.decode(data)) is None:
                self.message_handler.databuffer = b''
                raise ModbusIOException("Unable to decode request")
            result.slave_id = self.message_handler.incoming_dev_id
            result.transaction_id = self.message_handler.incoming_tid
            Log.debug("Frame advanced, resetting header!!")
            self.message_handler.databuffer = self.message_handler.databuffer[used_len:]
            if tid and result.transaction_id and tid != result.transaction_id:
                self.message_handler.databuffer = b''
            else:
                callback(result)  # defer or push to a thread?

    def buildPacket(self, message: ModbusRequest | ModbusResponse) -> bytes:
        """Create a ready to send modbus packet."""
        return self.message_handler.buildPacket(message)
