"""Framer implementations.

The implementation is responsible for encoding/decoding requests/responses.

According to the selected type of modbus frame a prefix/suffix is added/removed
"""
from __future__ import annotations

from enum import Enum

from pymodbus.exceptions import ModbusIOException
from pymodbus.logging import Log
from pymodbus.pdu import DecodePDU, ModbusPDU


class FramerType(str, Enum):
    """Type of Modbus frame."""

    ASCII = "ascii"
    RTU = "rtu"
    SOCKET = "socket"
    TLS = "tls"


class FramerBase:
    """Intern base."""

    EMPTY = b''
    MIN_SIZE = 0

    def __init__(
        self,
        decoder: DecodePDU,
    ) -> None:
        """Initialize a ADU (framer) instance."""
        self.decoder = decoder

    def decode(self, _data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU.

        returns:
            used_len (int) or 0 to read more
            dev_id,
            tid,
            modbus request/response (bytes)
        """
        return 0, 0, 0, self.EMPTY

    def encode(self, payload: bytes, _dev_id: int, _tid: int) -> bytes:
        """Encode ADU.

        returns:
            modbus ADU (bytes)
        """
        return payload

    def buildFrame(self, message: ModbusPDU) -> bytes:
        """Create a ready to send modbus packet.

        :param message: The populated request/response to send
        """
        data = message.function_code.to_bytes(1,'big') + message.encode()
        frame = self.encode(data, message.dev_id, message.transaction_id)
        return frame

    def handleFrame(self, data: bytes, exp_devid: int, exp_tid: int) -> tuple[int, ModbusPDU | None]:
        """Process incoming data."""
        used_len = 0
        while True:
            if used_len >= len(data):
                return used_len, None
            Log.debug("Processing: {}", data, ":hex")
            data_len, dev_id, tid, frame_data = self.decode(data)
            used_len += data_len
            if not data_len or not frame_data:
                return used_len, None
            if exp_devid and dev_id != exp_devid:
                Log.error(
                    f"ERROR: request ask for id={exp_devid} but got id={dev_id}, Skipping."
                )
                continue
            if exp_tid and tid and tid != exp_tid:
                Log.error(
                    f"ERROR: request ask for transaction_id={exp_tid} but got id={tid}, Skipping."
                )
                continue
            if (pdu := self.decoder.decode(frame_data)) is None:
                raise ModbusIOException("Unable to decode request")
            pdu.dev_id = dev_id
            pdu.transaction_id = tid
            return used_len, pdu
