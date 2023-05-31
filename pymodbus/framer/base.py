"""Framer start."""
# pylint: disable=missing-type-doc
from typing import Any, Dict, Union

from pymodbus.factory import ClientDecoder, ServerDecoder


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
        decoder: Union[ClientDecoder, ServerDecoder],
        client=None,
    ) -> None:
        """Initialize a new instance of the framer.

        :param decoder: The decoder implementation to use
        """
        self.decoder = decoder
        self.client = client
        self._header: Dict[str, Any] = {}

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

    def sendPacket(self, message):
        """Send packets on the bus.

        With 3.5char delay between frames
        :param message: Message to be sent over the bus
        :return:
        """
        return self.client.send(message)

    def recvPacket(self, size):
        """Receive packet from the bus.

        With specified len
        :param size: Number of bytes to read
        :return:
        """
        return self.client.recv(size)
