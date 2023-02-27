"""Framer start."""
# pylint: disable=missing-type-doc


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

    def __init__(self, decoder, client=None):
        """Initialize a new instance of the framer.

        :param decoder: The decoder implementation to use
        """
        self.decoder = decoder
        self.client = client

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
