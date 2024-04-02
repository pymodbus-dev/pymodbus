"""Framer implementations.

The implementation is responsible for encoding/decoding requests/responses.

According to the selected type of modbus frame a prefix/suffix is added/removed
"""
from __future__ import annotations


class FramerBase:
    """Intern base."""

    EMPTY = b''

    def __init__(self) -> None:
        """Initialize a ADU instance."""

    def decode(self, data: bytes) -> tuple[int, int, int, bytes]:
        """Decode ADU.

        returns:
            used_len (int) or 0 to read more
            transaction_id (int) or 0
            device_id (int) or 0
            modbus request/response (bytes)
        """
        raise RuntimeError("NOT IMPLEMENTED!")

    def encode(self, pdu: bytes, dev_id: int, tid: int) -> bytes:
        """Encode ADU.

        returns:
            modbus ADU (bytes)
        """
        raise RuntimeError("NOT IMPLEMENTED!")
