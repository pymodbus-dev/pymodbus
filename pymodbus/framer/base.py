"""Framer implementations.

The implementation is responsible for encoding/decoding requests/responses.

According to the selected type of modbus frame a prefix/suffix is added/removed
"""
from __future__ import annotations

from abc import abstractmethod

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.logging import Log
from pymodbus.pdu import ModbusRequest, ModbusResponse


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
        self.dev_ids = dev_ids
        self.incoming_dev_id = 0
        self.incoming_tid = 0
        self.databuffer = b""

    def decode(self, data: bytes) -> tuple[int, bytes]:
        """Decode ADU.

        returns:
            used_len (int) or 0 to read more
            modbus request/response (bytes)
        """
        if (data_len := len(data)) < self.MIN_SIZE:
          Log.debug("Very short frame (NO MBAP): {} wait for more data", data, ":hex")
          return 0, self.EMPTY
        used_len, res_data = self.specific_decode(data, data_len)
        if not res_data:
            self.incoming_dev_id = 0
            self.incoming_tid = 0
        return used_len, res_data

    @abstractmethod
    def specific_decode(self, data: bytes, data_len: int) -> tuple[int, bytes]:
        """Decode ADU.

        returns:
            used_len (int) or 0 to read more
            modbus request/response (bytes)
        """


    @abstractmethod
    def encode(self, pdu: bytes, dev_id: int, tid: int) -> bytes:
        """Encode ADU.

        returns:
            modbus ADU (bytes)
        """

    def buildPacket(self, message: ModbusRequest | ModbusResponse) -> bytes:
        """Create a ready to send modbus packet.

        :param message: The populated request/response to send
        """
        data = message.function_code.to_bytes(1,'big') + message.encode()
        packet = self.encode(data, message.slave_id, message.transaction_id)
        return packet
