"""Contains base classes for modbus request/response/error packets."""
from __future__ import annotations

import asyncio

from ..datastore import ModbusServerContext
from ..exceptions import ModbusIOException, NotImplementedException


class ModbusPDU:
    """Base class for all Modbus messages."""

    function_code: int = 0
    sub_function_code: int = -1
    rtu_frame_size: int = 0
    rtu_byte_count_pos: int = 0

    def __init__(self,
            dev_id: int = 0,
            transaction_id: int = 0,
            address: int = 0,
            count: int = 0,
            bits: list[bool] | None = None,
            registers: list[int] | None = None,
            status: int = 1,
        ) -> None:
        """Initialize the base data for a modbus request."""
        self.dev_id: int = dev_id
        if dev_id > 255:
            raise ModbusIOException(f"Invalid ID {dev_id}")
        self.transaction_id: int = transaction_id
        self.address: int = address
        self.bits: list[bool] = bits or []
        self.registers: list[int] = registers or []
        self.count: int = count or len(self.registers)
        self.status: int = status
        self.exception_code: int = 0
        self.fut: asyncio.Future
        self.retries: int = 0

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return self.function_code > 0x80

    def verifyCount(self, max_count: int, count: int = -1) -> None:
        """Validate API supplied count."""
        if count == -1:
            count = self.count
        if not 1 <= count <= max_count:
            raise ValueError(f"1 < count {count} < {max_count} !")

    def verifyAddress(self, address: int = -1) -> None:
        """Validate API supplied address."""
        if address == -1:
            address = self.address
        if not 0 <= address <= 65535:
            raise ValueError(f"0 < address {address} < 65535 !")

    @classmethod
    def decode_sub_function_code(cls, data: bytes) -> int:
        """Decode sub function code."""
        _ = data
        return -1

    def __str__(self) -> str:
        """Build a representation of a Modbus response."""
        return (
            f"{self.__class__.__name__}("
            f"dev_id={self.dev_id}, "
            f"transaction_id={self.transaction_id}, "
            f"address={self.address}, "
            f"count={self.count}, "
            f"bits={self.bits!s}, "
            f"registers={self.registers!s}, "
            f"status={self.status!s}, "
            f"retries={self.retries})"
        )

    def get_response_pdu_size(self) -> int:
        """Calculate response pdu size."""
        return 0

    def encode(self) -> bytes:
        """Encode the message."""
        return b''

    def decode(self, data: bytes) -> None:
        """Decode data part of the message."""

    async def datastore_update(self, context: ModbusServerContext, device_id: int) -> ModbusPDU:
        """Update diagnostic request on the given device."""
        _ = context, device_id
        raise NotImplementedException(
            f"update datastore called wrongly {self.__class__.__name__}"
        )

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
