"""Framer start."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer.base import FramerBase
from pymodbus.logging import Log
from pymodbus.pdu import ModbusRequest, ModbusResponse


if TYPE_CHECKING:
    from pymodbus.client.base import ModbusBaseSyncClient

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
        client: ModbusBaseSyncClient,
    ) -> None:
        """Initialize a new instance of the framer.

        :param decoder: The decoder implementation to use
        """
        self.decoder = decoder
        self.client = client
        self._buffer = b""
        self.message_handler: FramerBase
        self.tid = 0
        self.dev_id = 0

    def _validate_slave_id(self, slaves: list) -> bool:
        """Validate if the received data is valid for the client.

        :param slaves: list of slave id for which the transaction is valid
        :param single: Set to true to treat this as a single context
        :return:
        """
        if not slaves or 0 in slaves or 0xFF in slaves:
            # Handle Modbus TCP slave identifier (0x00 0r 0xFF)
            # in asynchronous requests
            return True
        return self.dev_id in slaves

    def sendPacket(self, message: bytes):
        """Send packets on the bus.

        With 3.5char delay between frames
        :param message: Message to be sent over the bus
        :return:
        """
        return self.client.send(message)

    def recvPacket(self, size: int) -> bytes:
        """Receive packet from the bus.

        With specified len
        :param size: Number of bytes to read
        :return:
        """
        packet = self.client.recv(size)
        self.client.last_frame_end = round(time.time(), 6)
        return packet

    def resetFrame(self):
        """Reset the entire message frame.

        This allows us to skip ovver errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        Log.debug(
            "Resetting frame - Current Frame in buffer - {}", self._buffer, ":hex"
        )
        self._buffer = b""
        self.dev_id = 0
        self.tid = 0

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
        self._buffer += data
        if self._buffer == b'':
            return
        if not isinstance(slave, (list, tuple)):
            slave = [slave]
        while True:
            if self._buffer == b'':
                return
            used_len, data = self.message_handler.decode(self._buffer)
            self.dev_id = self.message_handler.incoming_dev_id
            if used_len:
                self._buffer = self._buffer[used_len:]
            if not data:
                return
            self.dev_id = self.message_handler.incoming_dev_id
            self.tid = self.message_handler.incoming_tid
            if not self._validate_slave_id(slave):
                Log.debug("Not a valid slave id - {}, ignoring!!", self.message_handler.incoming_dev_id)
                self.resetFrame()
                continue
            if (result := self.decoder.decode(data)) is None:
                self.resetFrame()
                raise ModbusIOException("Unable to decode request")
            result.slave_id = self.dev_id
            result.transaction_id = self.tid
            Log.debug("Frame advanced, resetting header!!")
            self._buffer = self._buffer[used_len:]
            if tid and result.transaction_id and tid != result.transaction_id:
                self.resetFrame()
            else:
                callback(result)  # defer or push to a thread?

    def buildPacket(self, message: ModbusRequest | ModbusResponse) -> bytes:
        """Create a ready to send modbus packet.

        :param message: The populated request/response to send
        """
        data = message.function_code.to_bytes(1,'big') + message.encode()
        packet = self.message_handler.encode(data, message.slave_id, message.transaction_id)
        return packet
