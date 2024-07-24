"""Framer start."""
# pylint: disable=missing-type-doc
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

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

    name = ""

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
        self._header: dict[str, Any]
        self._reset_header()
        self._buffer = b""
        self.message_handler: FramerBase

    def _reset_header(self) -> None:
        self._header = {
            "lrc": "0000",
            "len": 0,
            "uid": 0x00,
            "tid": 0,
            "pid": 0,
            "crc": b"\x00\x00",
        }

    def _validate_slave_id(self, slaves: list, single: bool) -> bool:
        """Validate if the received data is valid for the client.

        :param slaves: list of slave id for which the transaction is valid
        :param single: Set to true to treat this as a single context
        :return:
        """
        if single:
            return True
        if 0 in slaves or 0xFF in slaves:
            # Handle Modbus TCP slave identifier (0x00 0r 0xFF)
            # in asynchronous requests
            return True
        return self._header["uid"] in slaves

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
        self._header = {
            "lrc": "0000",
            "crc": b"\x00\x00",
            "len": 0,
            "uid": 0x00,
            "pid": 0,
            "tid": 0,
        }

    def populateResult(self, result):
        """Populate the modbus result header.

        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        """
        result.slave_id = self._header.get("uid", 0)
        result.transaction_id = self._header.get("tid", 0)
        result.protocol_id = self._header.get("pid", 0)

    def processIncomingPacket(self, data: bytes, callback, slave, single=False, tid=None):
        """Process new packet pattern.

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 // N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        :param slave: Process if slave id matches, ignore otherwise (could be a
               list of slave ids (server) or single slave id(client/server))
        :param single: multiple slave ?
        :param tid: transaction id
        :raises ModbusIOException:
        """
        Log.debug("Processing: {}", data, ":hex")
        self._buffer += data
        if self._buffer == b'':
            return
        if not isinstance(slave, (list, tuple)):
            slave = [slave]
        self.frameProcessIncomingPacket(single, callback, slave, tid=tid)

    def frameProcessIncomingPacket(
        self, _single, _callback, _slave, tid=None
    ) -> None:
        """Process new packet pattern."""

    def buildPacket(self, message: ModbusRequest | ModbusResponse) -> bytes:
        """Create a ready to send modbus packet.

        :param message: The populated request/response to send
        """
        data = message.function_code.to_bytes(1,'big') + message.encode()
        packet = self.message_handler.encode(data, message.slave_id, message.transaction_id)
        return packet
