"""ModbusMessage layer.

is extending ModbusProtocol to handle receiving and sending of messsagees.

ModbusMessage provides a unified interface to send/receive Modbus requests/responses.
"""
from __future__ import annotations

import struct

from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.logging import Log
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

    function_codes: list[int] = []

    @classmethod
    def set_legal_function_codes(cls, function_codes: list[int]):
        """Set legal function codes."""
        cls.function_codes = function_codes

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
                return MessageRTU.check_CRC(data, crc_val)
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


    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode message."""
        resp = None
        if len(data) < 4:
            return 0, 0, 0, b''

        def callback(result):
            """Set result."""
            nonlocal resp
            resp = result

        self._legacy_decode(callback, [0])
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
