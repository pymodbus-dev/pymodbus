"""Modbus RTU frame implementation."""
from __future__ import annotations

import struct

from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.framer.base import FramerBase
from pymodbus.logging import Log


class FramerRTU(FramerBase):
    """Modbus RTU frame type.

    [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC ]
      3.5 chars     1b         1b               Nb      2b

    * Note: due to the USB converter and the OS drivers, timing cannot be quaranteed
    neither when receiving nor when sending.
    """

    MIN_SIZE = 5

    def __init__(self) -> None:
        """Initialize a ADU instance."""
        super().__init__()
        self.broadcast: bool = False
        self.dev_ids: list[int]
        self.fc_calc: dict[int, int]

    def set_dev_ids(self, dev_ids: list[int]):
        """Set/update allowed device ids."""
        if 0 in dev_ids:
            self.broadcast = True
        self.dev_ids = dev_ids

    def set_fc_calc(self, fc: int, msg_size: int, count_pos: int):
        """Set/Update function code information."""
        self.fc_calc[fc] = msg_size if not count_pos else -count_pos


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

    def _legacy_decode(self, callback, slave):  # noqa: C901
        """Process new packet pattern."""

        def is_frame_ready(self):
            """Check if we should continue decode logic."""
            size = self._header.get("len", 0)
            if not size and len(self._buffer) > self._hsize:
                try:
                    self._header["uid"] = int(self._buffer[0])
                    self._header["tid"] = int(self._buffer[0])
                    func_code = int(self._buffer[1])
                    pdu_class = self.decoder.lookupPduClass(func_code)
                    size = pdu_class.calculateRtuFrameSize(self._buffer)
                    self._header["len"] = size

                    if len(self._buffer) < size:
                        raise IndexError
                    self._header["crc"] = self._buffer[size - 2 : size]
                except IndexError:
                    return False
            return len(self._buffer) >= size if size > 0 else False

        def get_frame_start(self, slaves, broadcast, skip_cur_frame):
            """Scan buffer for a relevant frame start."""
            start = 1 if skip_cur_frame else 0
            if (buf_len := len(self._buffer)) < 4:
                return False
            for i in range(start, buf_len - 3):  # <slave id><function code><crc 2 bytes>
                if not broadcast and self._buffer[i] not in slaves:
                    continue
                if (
                    self._buffer[i + 1] not in self.function_codes
                    and (self._buffer[i + 1] - 0x80) not in self.function_codes
                ):
                    continue
                if i:
                    self._buffer = self._buffer[i:]  # remove preceding trash.
                return True
            if buf_len > 3:
                self._buffer = self._buffer[-3:]
            return False

        def check_frame(self):
            """Check if the next frame is available."""
            try:
                self._header["uid"] = int(self._buffer[0])
                self._header["tid"] = int(self._buffer[0])
                func_code = int(self._buffer[1])
                pdu_class = self.decoder.lookupPduClass(func_code)
                size = pdu_class.calculateRtuFrameSize(self._buffer)
                self._header["len"] = size

                if len(self._buffer) < size:
                    raise IndexError
                self._header["crc"] = self._buffer[size - 2 : size]
                frame_size = self._header["len"]
                data = self._buffer[: frame_size - 2]
                crc = self._header["crc"]
                crc_val = (int(crc[0]) << 8) + int(crc[1])
                return FramerRTU.check_CRC(data, crc_val)
            except (IndexError, KeyError, struct.error):
                return False

        self._buffer = b''  # pylint: disable=attribute-defined-outside-init
        broadcast = not slave[0]
        skip_cur_frame = False
        while get_frame_start(self, slave, broadcast, skip_cur_frame):
            self._header: dict = {"uid": 0x00, "len": 0, "crc": b"\x00\x00"}  # pylint: disable=attribute-defined-outside-init
            if not is_frame_ready(self):
                Log.debug("Frame - not ready")
                break
            if not check_frame(self):
                Log.debug("Frame check failed, ignoring!!")
                # x = self._buffer
                # self.resetFrame()
                # self._buffer = x
                skip_cur_frame = True
                continue
            start = 0x01  # self._hsize
            end = self._header["len"] - 2
            buffer = self._buffer[start:end]
            if end > 0:
                Log.debug("Getting Frame - {}", buffer, ":hex")
                data = buffer
            else:
                data = b""
            if (result := ClientDecoder().decode(data)) is None:
                raise ModbusIOException("Unable to decode request")
            result.slave_id = self._header["uid"]
            result.transaction_id = self._header["tid"]
            self._buffer = self._buffer[self._header["len"] :]  # pylint: disable=attribute-defined-outside-init
            Log.debug("Frame advanced, resetting header!!")
            callback(result)  # defer or push to a thread?


    def hunt_frame_start(self, skip_cur_frame: bool, data: bytes) -> int:
        """Scan buffer for a relevant frame start."""
        buf_len = len(data)
        for i in range(1 if skip_cur_frame else 0, buf_len - self.MIN_SIZE):
            if not (self.broadcast or data[i] in self.dev_ids):
                continue
            if (_fc := data[i + 1]) not in self.fc_calc:
                continue
            return i
        return -i

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU."""
        if len(data) < self.MIN_SIZE:
            return 0, 0, 0, b''

        while (i := self.hunt_frame_start(False, data)) > 0:
            pass
        return -i, 0, 0, b''


    def encode(self, pdu: bytes, device_id: int, _tid: int) -> bytes:
        """Encode ADU."""
        packet = device_id.to_bytes(1,'big') + pdu
        return packet + FramerRTU.compute_CRC(packet).to_bytes(2,'big')

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
