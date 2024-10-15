"""Contains base classes for modbus request/response/error packets."""
from __future__ import annotations

import asyncio
import struct
from abc import abstractmethod

from pymodbus.exceptions import NotImplementedException
from pymodbus.logging import Log


# --------------------------------------------------------------------------- #
# Base PDUs
# --------------------------------------------------------------------------- #
class ModbusPDU:
    """Base class for all Modbus messages."""

    function_code: int = 0
    _rtu_frame_size: int = 0
    _rtu_byte_count_pos: int = 0

    def __init__(self, slave: int, transaction: int, skip_encode: bool) -> None:
        """Initialize the base data for a modbus request."""
        self.transaction_id = transaction
        self.slave_id = slave
        self.skip_encode = skip_encode
        self.fut: asyncio.Future | None = None

    @abstractmethod
    def encode(self) -> bytes:
        """Encode the message."""

    @abstractmethod
    def decode(self, data: bytes) -> None:
        """Decode data part of the message."""

    def doException(self, exception: int) -> ExceptionResponse:
        """Build an error response based on the function."""
        exc = ExceptionResponse(self.function_code, exception)
        Log.error("Exception response {}", exc)
        return exc

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


class ModbusResponse(ModbusPDU):
    """Base class for a modbus response PDU."""

    def __init__(self, slave, transaction, skip_encode):
        """Proxy the lower level initializer.

        :param slave: Modbus slave slave ID

        """
        super().__init__(slave, transaction, skip_encode)
        self.bits = []
        self.registers = []
        self.request = None

    @abstractmethod
    def encode(self):
        """Encode the message."""

    @abstractmethod
    def decode(self, data):
        """Decode data part of the message."""

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return self.function_code > 0x80


# --------------------------------------------------------------------------- #
# Exception PDUs
# --------------------------------------------------------------------------- #
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
    def decode(cls, code):
        """Give an error code, translate it to a string error name."""
        values = {
            v: k
            for k, v in iter(cls.__dict__.items())
            if not k.startswith("__") and not callable(v)
        }
        return values.get(code, None)


class ExceptionResponse(ModbusResponse):
    """Base class for a modbus exception PDU."""

    ExceptionOffset = 0x80
    _rtu_frame_size = 5

    def __init__(self, function_code, exception_code=None, slave=1, transaction=0, skip_encode=False):
        """Initialize the modbus exception response.

        :param function_code: The function to build an exception response for
        :param exception_code: The specific modbus exception to return
        """
        super().__init__(slave, transaction, skip_encode)
        self.original_code = function_code
        self.function_code = function_code | self.ExceptionOffset
        self.exception_code = exception_code

    def encode(self):
        """Encode a modbus exception response.

        :returns: The encoded exception packet
        """
        return struct.pack(">B", self.exception_code)

    def decode(self, data):
        """Decode a modbus exception response."""
        self.exception_code = int(data[0])

    def __str__(self):
        """Build a representation of an exception response."""
        message = ModbusExceptions.decode(self.exception_code)
        parameters = (self.function_code, self.original_code, message)
        return (
            "Exception Response(%d, %d, %s)"  # pylint: disable=consider-using-f-string
            % parameters
        )


class IllegalFunctionRequest(ModbusPDU):
    """Define the Modbus slave exception type "Illegal Function".

    This exception code is returned if the slave::

        - does not implement the function code **or**
        - is not in a state that allows it to process the function
    """

    ErrorCode = 1

    def __init__(self, function_code, slave, transaction, xskip_encode):
        """Initialize a IllegalFunctionRequest.

        :param function_code: The function we are erroring on
        """
        super().__init__(slave, transaction, xskip_encode)
        self.function_code = function_code

    def decode(self, _data):
        """Decode so this failure will run correctly."""

    def encode(self):
        """Decode so this failure will run correctly."""

    async def execute(self, _context):
        """Build an illegal function request error response.

        :returns: The error response packet
        """
        return ExceptionResponse(self.function_code, self.ErrorCode)
