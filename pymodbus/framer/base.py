"""Framer implementations.

The implementation is responsible for encoding/decoding requests/responses.

According to the selected type of modbus frame a prefix/suffix is added/removed
"""
from __future__ import annotations

from abc import abstractmethod


class FramerBase:
    """Intern base."""

    EMPTY = b''

    def __init__(self) -> None:
        """Initialize a ADU instance."""

    def set_dev_ids(self, _dev_ids: list[int]):
        """Set/update allowed device ids."""

    def set_fc_calc(self, _fc: int, _msg_size: int, _count_pos: int):
        """Set/Update function code information."""

    @abstractmethod
    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU.

        returns:
            used_len (int) or 0 to read more
            transaction_id (int) or 0
            device_id (int) or 0
            modbus request/response (bytes)
        """

    @abstractmethod
    def encode(self, pdu: bytes, dev_id: int, tid: int) -> bytes:
        """Encode ADU.

        returns:
            modbus ADU (bytes)
        """
