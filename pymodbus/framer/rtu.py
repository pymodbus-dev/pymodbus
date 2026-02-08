"""Modbus RTU frame implementation."""
from __future__ import annotations

from ..logging import Log
from .base import FramerBase


class FramerRTU(FramerBase):
    """Modbus RTU frame type.

    Layout::

        [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC ]
          3.5 chars     1b         1b               Nb      2b

    .. note::

            due to the USB converter and the OS drivers, timing cannot be quaranteed
            neither when receiving nor when sending.

    Decoding is a complicated process because the RTU frame does not have a fixed prefix
    only suffix, therefore it is necessary to decode the content of the frame to get length etc.
    There are some protocol restrictions that help with the detection.

    For client:
       - a request causes 1 response !
       - Multiple requests are NOT allowed (master controlled protocol)
       - the server will not retransmit responses

    this means decoding is always exactly 1 frame (response)

    For server (Single device)
       - only 1 request allowed (master controlled protocol)
       - the client (master) may retransmit but in larger time intervals

    this means decoding is always exactly 1 frame (request)

    For server (Multidrop line --> devices in parallel)
       - only 1 request allowed (master controlled protocol)
       - other devices will send responses (unknown dev_id)
       - the client (master) may retransmit but in larger time intervals

    this means decoding is always exactly 1 frame request, however some requests
    will be for unknown devices, which must be ignored together with the
    response from the unknown device.

    Recovery from bad cabling and unstable USB etc is important,
    the following scenarios is possible:

        - garble data before frame (extra data preceding)
        - garble data in frame (wrong CRC)
        - garble data after frame (extra data after correct frame)

    decoding assumes the frame is sound, and if not enters a hunting mode.

    .. Danger:: framerRTU only offer limited support for running the server in parallel with other devices.

    """

    MIN_SIZE = 4  # <device id><function code><crc 2 bytes>
    device_ids: list[int] = [] # will be converted to instance variable

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

    def setMultidrop(self, device_ids: list[int]):
        """Activate multidrop support."""
        self.device_ids = device_ids

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU."""
        data_len = len(data)
        for used_len in range(data_len):
            if data_len - used_len < self.MIN_SIZE:
                Log.debug("Short frame: {} wait for more data", data, ":hex")
                return 0, 0, 0, self.EMPTY
            dev_id = int(data[used_len])
            if self.device_ids and dev_id not in self.device_ids:
                return data_len, 0, 0, self.EMPTY
            if not (pdu_class := self.decoder.lookupPduClass(data[used_len:])):
                continue
            if not (size := pdu_class.calculateRtuFrameSize(data[used_len:])):
                Log.debug("Frame - rtu_byte_count_pos wrong")
                return 0, dev_id, 0, self.EMPTY
            if data_len < used_len +size:
                Log.debug("Frame - not ready")
                return 0, dev_id, 0, self.EMPTY
            for test_len in range(data_len, used_len + size - 1, -1):
                start_crc = test_len -2
                crc = data[start_crc : start_crc + 2]
                crc_val = (int(crc[0]) << 8) + int(crc[1])
                if not FramerRTU.check_CRC(data[used_len : start_crc], crc_val):
                    Log.debug("Frame check failed, possible garbage after frame, testing..")
                    continue
                return data_len, dev_id, 0, data[used_len + 1 : start_crc]
        return 0, 0, 0, self.EMPTY


    def encode(self, payload: bytes, device_id: int, _tid: int) -> bytes:
        """Encode ADU."""
        frame = device_id.to_bytes(1,'big') + payload
        return frame + FramerRTU.compute_CRC(frame).to_bytes(2,'big')

    @classmethod
    def check_CRC(cls, data: bytes, check: int) -> bool:
        """Check if the data matches the passed in CRC.

        :param data: The data to create a crc16 of
        :param check: The CRC to verify
        :returns: True if matched, False otherwise
        """
        return cls.compute_CRC(data) == check

    @classmethod
    def compute_CRC(cls, data: bytes) -> int:
        """Compute a crc16 on the passed in bytes.

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

FramerRTU.crc16_table = FramerRTU.generate_crc16_table()
