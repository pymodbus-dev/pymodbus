"""Contains exceptionResponse class for modbus."""

from __future__ import annotations

import struct

from .pdu import ModbusPDU


class ExceptionResponse(ModbusPDU):
    """Base class for a modbus exception PDU."""

    @classmethod
    def x_calculateRtuFrameSize(cls, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 5

    def __init__(
        self,
        function_code: int,
        exception_code: int = 0,
        device_id: int = 1,
        transaction: int = 0,
    ) -> None:
        """Initialize the modbus exception response."""
        super().__init__(transaction_id=transaction, dev_id=device_id)
        self.function_code = function_code | 0x80
        self.exception_code = exception_code

    def __str__(self) -> str:
        """Build a representation of an exception response."""
        return (
            f"{self.__class__.__name__}("
            f"dev_id={self.dev_id}, "
            f"function_code={self.function_code}, "
            f"exception_code={self.exception_code})"
        )

    def x_encode(self) -> bytes:
        """Encode a modbus exception response."""
        return struct.pack(">B", self.exception_code)

    def x_decode(self, data: bytes) -> None:
        """Decode data part of the message."""
        _ = data

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return True

    def from_frame(self, is_request: bool, data: bytes) -> int:
        """Decode a modbus exception response."""
        _ = is_request
        self.function_code = int(data[0])
        self.exception_code = int(data[1])
        return 5
