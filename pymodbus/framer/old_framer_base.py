"""Framer start."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.framer.base import FramerBase
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
        new_framer,
    ) -> None:
        """Initialize a new instance of the framer.

        :param decoder: The decoder implementation to use
        """
        self.message_handler: FramerBase = new_framer(decoder, [0])

    @property
    def incoming_dev_id(self) -> int:
        """Return dev id."""
        return self.message_handler.incoming_dev_id

    @property
    def incoming_tid(self) -> int:
        """Return tid."""
        return self.message_handler.incoming_tid

    def processIncomingPacket(self, data: bytes, callback, slave, tid=None):
        """Process new packet pattern."""
        self.message_handler.processIncomingPacket(data, callback, slave, tid=tid)

    def buildPacket(self, message: ModbusRequest | ModbusResponse) -> bytes:
        """Create a ready to send modbus packet."""
        return self.message_handler.buildPacket(message)
