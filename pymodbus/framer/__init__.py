from pymodbus.interfaces import IModbusFramer
import struct

# Unit ID, Function Code
BYTE_ORDER = '>'
FRAME_HEADER = 'BB'

# Transaction Id, Protocol ID, Length, Unit ID, Function Code
SOCKET_FRAME_HEADER = BYTE_ORDER + 'HHH' + FRAME_HEADER


class ModbusFramer(IModbusFramer):
    """
    Base Framer class
    """

    def _validate_unit_id(self, units, single):
        """
        Validates if the received data is valid for the client
        :param units: list of unit id for which the transaction is valid
        :param single: Set to true to treat this as a single context
        :return:         """

        if single:
            return True
        else:
            if 0 in units or 0xFF in units:
                # Handle Modbus TCP unit identifier (0x00 0r 0xFF)
                # in async requests
                return True
            return self._header['uid'] in units

    def sendPacket(self, message):
        """
        Sends packets on the bus with 3.5char delay between frames
        :param message: Message to be sent over the bus
        :return:
        """
        return self.client.send(message)

    def recvPacket(self, size):
        """
        Receives packet from the bus with specified len
        :param size: Number of bytes to read
        :return:
        """
        return self.client.recv(size)
