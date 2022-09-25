"""Framer start."""
# pylint: disable=missing-type-doc
from pymodbus.interfaces import IModbusFramer


# Unit ID, Function Code
BYTE_ORDER = ">"
FRAME_HEADER = "BB"

# Transaction Id, Protocol ID, Length, Unit ID, Function Code
SOCKET_FRAME_HEADER = BYTE_ORDER + "HHH" + FRAME_HEADER

# Function Code
TLS_FRAME_HEADER = BYTE_ORDER + "B"


class ModbusFramer(IModbusFramer):
    """Base Framer class."""

    name = ""

    def _validate_unit_id(self, units, single):
        """Validate if the received data is valid for the client.

        :param units: list of unit id for which the transaction is valid
        :param single: Set to true to treat this as a single context
        :return:
        """
        if single:
            return True
        if 0 in units or 0xFF in units:
            # Handle Modbus TCP unit identifier (0x00 0r 0xFF)
            # in asynchronous requests
            return True
        return self._header["uid"] in units  # pylint: disable=no-member

    def sendPacket(self, message):  # pylint: disable=invalid-name
        """Send packets on the bus.

        With 3.5char delay between frames
        :param message: Message to be sent over the bus
        :return:
        """
        return self.client.send(message)  # pylint: disable=no-member

    def recvPacket(self, size):  # pylint: disable=invalid-name
        """Receive packet from the bus.

        With specified len
        :param size: Number of bytes to read
        :return:
        """
        return self.client.recv(size)  # pylint: disable=no-member
