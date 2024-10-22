"""Contains base classes for modbus request/response/error packets."""
from __future__ import annotations

import asyncio
import struct
from abc import abstractmethod

from pymodbus.exceptions import NotImplementedException
from pymodbus.logging import Log


class ModbusPDU:
    """Base class for all Modbus messages."""

    function_code: int = 0
    sub_function_code: int = -1
    _rtu_frame_size: int = 0
    _rtu_byte_count_pos: int = 0

    def __init__(self) -> None:
        """Initialize the base data for a modbus request."""
        self.transaction_id: int
        self.slave_id: int
        self.skip_encode: bool
        self.bits: list[bool]
        self.registers: list[int]
        self.fut: asyncio.Future

    def setData(self, slave: int, transaction: int, skip_encode: bool) -> None:
        """Set data common for all PDU."""
        self.transaction_id = transaction
        self.slave_id = slave
        self.skip_encode = skip_encode

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
        if cls._rtu_frame_size:
            return cls._rtu_frame_size
        if cls._rtu_byte_count_pos:
            if len(data) < cls._rtu_byte_count_pos +1:
                return 0
            return int(data[cls._rtu_byte_count_pos]) + cls._rtu_byte_count_pos + 3
        raise NotImplementedException(
            f"Cannot determine RTU frame size for {cls.__name__}"
        )


class ModbusExceptions:  # pylint: disable=too-few-public-methods
    """An enumeration of the valid modbus exceptions."""

    IllegalFunction = 0x01
    IllegalAddress = 0x02
    IllegalValue = 0x03
    SlaveFailure = 0x04
    Acknowledge = 0x05
    SlaveBusy = 0x06
    NegativeAcknowledge = 0x07
    MemoryParityError = 0x08
    GatewayPathUnavailable = 0x0A
    GatewayNoResponse = 0x0B

    @classmethod
    def decode(cls, code: int) -> str | None:
        """Give an error code, translate it to a string error name."""
        values = {
            v: k
            for k, v in iter(cls.__dict__.items())
            if not k.startswith("__") and not callable(v)
        }
        return values.get(code, None)


class ExceptionResponse(ModbusPDU):
    """Base class for a modbus exception PDU."""

    _rtu_frame_size = 5

    def __init__(
            self,
            function_code: int,
            exception_code: int = 0,
            slave: int = 1,
            transaction: int = 0,
            skip_encode: bool = False) -> None:
        """Initialize the modbus exception response."""
        super().__init__()
        super().setData(slave, transaction, skip_encode)
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
        message = ModbusExceptions.decode(self.exception_code)
        return (
            f"Exception Response({self.function_code}, {self.function_code - 0x80}, {message})"
        )
