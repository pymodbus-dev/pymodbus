"""Contains base classes for modbus request/response/error packets."""
from __future__ import annotations

import asyncio
import struct
from abc import abstractmethod
from collections.abc import Sequence
from enum import Enum
from typing import cast

from pymodbus.exceptions import NotImplementedException
from pymodbus.logging import Log


class ModbusPDU:
    """Base class for all Modbus messages."""

    function_code: int = 0
    sub_function_code: int = -1
    rtu_frame_size: int = 0
    rtu_byte_count_pos: int = 0

    def __init__(self,
            slave_id: int = 0,
            transaction_id: int = 0,
            address: int = 0,
            count: int = 0,
            bits: list[bool] | None = None,
            registers: Sequence[int | bytes] | None = None,
            status: int = 1,
        ) -> None:
        """Initialize the base data for a modbus request."""
        self.slave_id: int = slave_id
        self.transaction_id: int = transaction_id
        self.address: int = address
        self.bits: list[bool] = bits if bits else []
        if not registers:
            registers = []
        self.registers: list[int] = cast(list[int], registers)
        for i, value in enumerate(registers):
            if isinstance(value, bytes):
                self.registers[i] = int.from_bytes(value, byteorder="big")
        self.count: int = count if count else len(registers)
        self.status: int = status
        self.fut: asyncio.Future

    def doException(self, exception: int) -> ExceptionResponse:
        """Build an error response based on the function."""
        exc = ExceptionResponse(self.function_code, exception)
        Log.error("Exception response {}", exc)
        return exc

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return self.function_code > 0x80

    def get_response_pdu_size(self) -> int:
        """Calculate response pdu size."""
        return 0

    @abstractmethod
    def encode(self) -> bytes:
        """Encode the message."""

    @abstractmethod
    def decode(self, data: bytes) -> None:
        """Decode data part of the message."""


    @classmethod
    def calculateRtuFrameSize(cls, data: bytes) -> int:
        """Calculate the size of a PDU."""
        if cls.rtu_frame_size:
            return cls.rtu_frame_size
        if cls.rtu_byte_count_pos:
            if len(data) < cls.rtu_byte_count_pos +1:
                return 0
            return int(data[cls.rtu_byte_count_pos]) + cls.rtu_byte_count_pos + 3
        raise NotImplementedException(
            f"Cannot determine RTU frame size for {cls.__name__}"
        )


class ModbusExceptions(int, Enum):
    """An enumeration of the valid modbus exceptions."""

    ILLEGAL_FUNCTION = 0x01
    ILLEGAL_ADDRESS = 0x02
    ILLEGAL_VALUE = 0x03
    SLAVE_FAILURE = 0x04
    ACKNOWLEDGE = 0x05
    SLAVE_BUSY = 0x06
    NEGATIVE_ACKNOWLEDGE = 0x07
    MEMORY_PARITY_ERROR = 0x08
    GATEWAY_PATH_UNAVIABLE = 0x0A
    GATEWAY_NO_RESPONSE = 0x0B


class ExceptionResponse(ModbusPDU):
    """Base class for a modbus exception PDU."""

    rtu_frame_size = 5

    def __init__(
            self,
            function_code: int,
            exception_code: int = 0,
            slave: int = 1,
            transaction: int = 0) -> None:
        """Initialize the modbus exception response."""
        super().__init__(transaction_id=transaction, slave_id=slave)
        self.function_code = function_code | 0x80
        self.exception_code = exception_code

    def encode(self) -> bytes:
        """Encode a modbus exception response."""
        return struct.pack(">B", self.exception_code)

    def decode(self, data: bytes) -> None:
        """Decode a modbus exception response."""
        self.exception_code = int(data[0])

    def __str__(self) -> str:
        """Build a representation of an exception response."""
        names = {data.value: data.name for data in ModbusExceptions}
        message = names[self.exception_code]
        return (
            f"Exception Response({self.function_code}, {self.function_code - 0x80}, {message})"
        )
