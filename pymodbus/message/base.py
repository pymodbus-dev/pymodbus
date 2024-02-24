"""ModbusMessage layer.

The message layer is responsible for encoding/decoding requests/responses.

According to the selected type of modbus frame a prefix/suffix is added/removed
"""
from __future__ import annotations

from abc import abstractmethod


class MessageBase:
    """Intern base."""

    def __init__(
        self,
        device_ids: list[int] | None,
        is_server: bool,
    ) -> None:
        """Initialize a message instance.

        :param device_ids: list of device id to accept (server only), None for all.
        """
        self.device_ids = device_ids
        self.is_server = is_server

    @abstractmethod
    def reset(self) -> None:
        """Clear internal handling."""

    @abstractmethod
    def decode(self, _data: bytes) -> tuple[int, int, int, bytes]:
        """Decode message.

        return:
            used_len (int) or 0 to read more
            transaction_id (int) or 0
            device_id (int) or 0
            modbus request/response (bytes)
        """

    @abstractmethod
    def encode(self, data: bytes, device_id: int, tid: int) -> bytes:
        """Decode message.

        return:
            modbus message (bytes)
        """
