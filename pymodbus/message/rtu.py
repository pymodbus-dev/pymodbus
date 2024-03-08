"""ModbusMessage layer.

is extending ModbusProtocol to handle receiving and sending of messsagees.

ModbusMessage provides a unified interface to send/receive Modbus requests/responses.
"""
from __future__ import annotations

from pymodbus.message.base import MessageBase


class MessageRTU(MessageBase):
    """Modbus RTU frame type.

    [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC ][  End Wait  ]
        3.5 chars     1b         1b               Nb      2b      3.5 chars

    Wait refers to the amount of time required to transmit at least x many
    characters.  In this case it is 3.5 characters.  Also, if we receive a
    wait of 1.5 characters at any point, we must trigger an error message.
    Also, it appears as though this message is little endian. The logic is
    simplified as the following::

    The following table is a listing of the baud wait times for the specified
    baud rates::

        ------------------------------------------------------------------
           Baud  1.5c (18 bits)   3.5c (38 bits)
        ------------------------------------------------------------------
           1200  15,000 ms        31,667 ms
           4800   3,750 ms         7,917 ms
           9600   1,875 ms         3,958 ms
          19200   0,938 ms         1,979 ms
          38400   0,469 ms         0,989 ms
         115200   0,156 ms         0,329 ms
        ------------------------------------------------------------------
        1 Byte = 8 bits + 1 bit parity + 2 stop bit = 11 bits

    * Note: due to the USB converter and the OS drivers, timing cannot be quaranteed
    neither when receiving nor when sending.
    """

    @classmethod
    def generate_crc16_table(cls) -> list[int]:
        """Generate a crc16 lookup table.

        .. note:: This will only be generated once
        """
        result = []
        for byte in range(256):
            crc = 0x0000
            for _ in range(8):
                if (byte ^ crc) & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
                byte >>= 1
            result.append(crc)
        return result
    crc16_table: list[int] = [0]

    def decode(self, _data: bytes) -> tuple[int, int, int, bytes]:
        """Decode message."""
        return 0, 0, 0, b''

    def encode(self, data: bytes, device_id: int, _tid: int) -> bytes:
        """Decode message."""
        packet = device_id.to_bytes(1,'big') + data
        return packet + MessageRTU.compute_CRC(packet).to_bytes(2,'big')

    @classmethod
    def check_CRC(cls, data: bytes, check: int) -> bool:
        """Check if the data matches the passed in CRC.

        :param data: The data to create a crc16 of
        :param check: The CRC to validate
        :returns: True if matched, False otherwise
        """
        return cls.compute_CRC(data) == check

    @classmethod
    def compute_CRC(cls, data: bytes) -> int:
        """Compute a crc16 on the passed in bytes.

        For modbus, this is only used on the binary serial protocols (in this
        case RTU).

        The difference between modbus's crc16 and a normal crc16
        is that modbus starts the crc value out at 0xffff.

        :param data: The data to create a crc16 of
        :returns: The calculated CRC
        """
        crc = 0xFFFF
        for data_byte in data:
            idx = cls.crc16_table[(crc ^ int(data_byte)) & 0xFF]
            crc = ((crc >> 8) & 0xFF) ^ idx
        swapped = ((crc << 8) & 0xFF00) | ((crc >> 8) & 0x00FF)
        return swapped

MessageRTU.crc16_table = MessageRTU.generate_crc16_table()
