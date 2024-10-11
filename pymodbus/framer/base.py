"""Framer implementations.

The implementation is responsible for encoding/decoding requests/responses.

According to the selected type of modbus frame a prefix/suffix is added/removed
"""
from __future__ import annotations

from enum import Enum

from pymodbus.exceptions import ModbusIOException
from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.logging import Log
from pymodbus.pdu import ModbusRequest, ModbusResponse


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
        decoder: ClientDecoder | ServerDecoder,
        dev_ids: list[int],
    ) -> None:
        """Initialize a ADU (framer) instance."""
        self.decoder = decoder
        if 0 in dev_ids:
            dev_ids = []
        self.dev_ids = dev_ids
        self.incoming_dev_id = 0
        self.incoming_tid = 0
        self.databuffer = b""

    def decode(self, _data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU.

        returns:
            used_len (int) or 0 to read more
            dev_id,
            tid,
            modbus request/response (bytes)
        """
        return 0, 0, 0, self.EMPTY

    def encode(self, pdu: bytes, dev_id: int, _tid: int) -> bytes:
        """Encode ADU.

        returns:
            modbus ADU (bytes)
        """
        if dev_id and dev_id not in self.dev_ids:
            self.dev_ids.append(dev_id)
        return pdu

    def buildFrame(self, message: ModbusRequest | ModbusResponse) -> bytes:
        """Create a ready to send modbus packet.

        :param message: The populated request/response to send
        """
        data = message.function_code.to_bytes(1,'big') + message.encode()
        frame = self.encode(data, message.slave_id, message.transaction_id)
        return frame

    def processIncomingFrame(self, data: bytes, callback, tid=None):
        """Process new packet pattern.

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.
        """
        self._processIncomingFrame(data, callback, tid=tid)

    def _processIncomingFrame(self, data: bytes, callback, tid=None):
        """Process new packet pattern.

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.
        """
        Log.debug("Processing: {}", data, ":hex")
        self.databuffer += data
        while True:
            if self.databuffer == b'':
                return
            used_len, self.incoming_dev_id, self.incoming_tid, frame_data = self.decode(self.databuffer)
            self.databuffer = self.databuffer[used_len:]
            if not frame_data:
                if used_len:
                    continue
                return
            if self.dev_ids and self.incoming_dev_id not in self.dev_ids:
                Log.debug("Not a valid slave id - {}, ignoring!!", self.incoming_dev_id)
                self.databuffer = b''
                continue
            if (result := self.decoder.decode(frame_data)) is None:
                self.databuffer = b''
                raise ModbusIOException("Unable to decode request")
            result.slave_id = self.incoming_dev_id
            result.transaction_id = self.incoming_tid
            Log.debug("Frame advanced, resetting header!!")
            if tid and result.transaction_id and tid != result.transaction_id:
                self.databuffer = b''
            else:
                callback(result)  # defer or push to a thread?
