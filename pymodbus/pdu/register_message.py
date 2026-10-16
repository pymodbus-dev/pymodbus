"""Register Reading Request/Response."""

from __future__ import annotations

import struct
from collections.abc import Sequence
from typing import cast

from ..constants import ExcCodes
from ..exceptions import ModbusIOException
from .pdu import DecodePDU, ModbusPdu, PDUexception, StoreGet, StoreSet


class PDUreadHoldingRegisters(ModbusPdu):
    """ReadHoldingRegisters."""

    function_code = 3
    MAX_COUNT = 125

    def __init__(
        self,
        *args,
        registers: Sequence[int] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.registers: Sequence[int] = registers or []

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", registers={self.registers}"

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 8 if is_request else int(data[offset + 2]) + 2 + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return struct.pack(">HH", self.address, self.count)
        result = struct.pack(">B", len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack(">H", register)
        return result

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count = struct.unpack(">HH", data[offset : offset + 4])
        else:
            self.registers = []
            if (data_len := int(data[offset])) >= len(data) - offset:
                raise ModbusIOException(
                    f"byte_count {data_len} > length of packet {len(data) - offset}",
                    function_code=self.function_code,
                )
            for i in range(1, data_len, 2):
                self.registers.append(
                    struct.unpack(">H", data[offset + i : offset + i + 2])[0]
                )

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        if not 1 <= self.count <= self.MAX_COUNT:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        values = await get_values(
            self.dev_id, self.function_code, self.address, self.count
        )
        if isinstance(values, ExcCodes):
            return PDUexception(self.dev_id, self.function_code, values)
        self.is_request = False
        return self


class PDUreadInputRegisters(PDUreadHoldingRegisters):
    """ReadInputRegisters."""

    function_code = 4
    MAX_COUNT = 125

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 8 if is_request else int(data[offset + 2]) + 2 + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return struct.pack(">HH", self.address, self.count)
        result = struct.pack(">B", len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack(">H", register)
        return result

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count = struct.unpack(">HH", data[offset : offset + 4])
        else:
            self.registers = []
            if (data_len := int(data[offset])) >= len(data) - offset:
                raise ModbusIOException(
                    f"byte_count {data_len} > length of packet {len(data) - offset}",
                    function_code=self.function_code,
                )
            for i in range(1, data_len, 2):
                self.registers.append(
                    struct.unpack(">H", data[offset + i : offset + i + 2])[0]
                )

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        if not 1 <= self.count <= self.MAX_COUNT:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        values = await get_values(
            self.dev_id, self.function_code, self.address, self.count
        )
        if isinstance(values, ExcCodes):
            return PDUexception(self.dev_id, self.function_code, values)
        self.is_request = False
        return self


class PDUreadWriteMultipleRegisters(ModbusPdu):
    """ReadWriteMultipleRegisters."""

    function_code = 23
    MAX_READ_COUNT = 125
    MAX_WRITE_COUNT = 121

    def __init__(
        self,
        *args,
        read_address: int = 0x00,
        read_count: int = 0,
        write_address: int = 0x00,
        write_registers: Sequence[int] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.write_registers: Sequence[int] = write_registers or []
        self.read_count: int = read_count
        self.read_address: int = read_address
        self.write_address: int = write_address
        self.write_count: int = len(write_registers) if write_registers else 0

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return (
            int(data[offset + 10]) + 10 + 3
            if is_request
            else int(data[offset + 2]) + 2 + 3
        )

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            result = struct.pack(
                ">HHHHB",
                self.read_address,
                self.read_count,
                self.write_address,
                self.write_count,
                self.write_count * 2,
            )
            for register in self.write_registers:
                result += struct.pack(">H", register)
            return result
        result = struct.pack(">B", len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack(">H", register)
        return result

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            (
                self.read_address,
                self.read_count,
                self.write_address,
                self.write_count,
                _,
            ) = struct.unpack(">HHHHB", data[offset : offset + 9])
            self.verifyCount(self.MAX_READ_COUNT, count=self.write_count)
            self.write_registers = [
                struct.unpack(">H", data[offset + i : offset + i + 2])[0]
                for i in range(
                    9, min(len(data) - offset, self.write_count * 2 + 9) - 1, 2
                )
            ]
        else:
            self.registers = []
            if (data_len := int(data[offset])) >= len(data) - offset:
                raise ModbusIOException(
                    f"byte_count {data_len} > length of packet {len(data) - offset}",
                    function_code=self.function_code,
                )
            for i in range(1, data_len, 2):
                self.registers.append(
                    struct.unpack(">H", data[offset + i : offset + i + 2])[0]
                )

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        if not (1 <= self.read_count <= 0x07D):
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        if not 1 <= self.write_count <= 0x079:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        rc = await set_values(
            self.dev_id, self.function_code, self.write_address, self.write_registers
        )
        if rc:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)

        registers = await get_values(
            self.dev_id, self.function_code, self.address, self.count
        )
        if isinstance(registers, ExcCodes):
            return PDUexception(self.dev_id, self.function_code, registers)
        self.is_request = False
        return self


class PDUwriteSingleRegister(PDUreadHoldingRegisters):
    """WriteSingleRegister."""

    function_code = 6

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 8

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return struct.pack(">HH", self.address, self.registers[0])

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        self.address, register = struct.unpack(">HH", data[offset : offset + 4])
        self.registers = [register]

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        if not 0 <= self.registers[0] <= 0xFFFF:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        rc = await set_values(
            self.dev_id, self.function_code, self.address, self.registers
        )
        if rc:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)

        registers = await get_values(self.dev_id, self.function_code, self.address, 1)
        if isinstance(registers, ExcCodes):
            return PDUexception(self.dev_id, self.function_code, registers)
        self.is_request = False
        return self


class PDUwriteMultipleRegisters(PDUreadHoldingRegisters):
    """WriteMultipleRegisters."""

    function_code = 16

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[offset + 6]) + 6 + 3 if is_request else 8

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            packet = struct.pack(">HHB", self.address, self.count, self.count * 2)
            for value in self.registers:
                packet += struct.pack(">H", value)
            return packet
        return struct.pack(">HH", self.address, self.count)

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count, byte_count = struct.unpack(
                ">HHB", data[offset : offset + 5]
            )
            self.registers = [
                struct.unpack(">H", data[offset + idx : offset + idx + 2])[0]
                for idx in range(5, min(len(data) - offset, byte_count + 5) - 1, 2)
            ]
        else:
            self.address, self.count = struct.unpack(">HH", data[offset : offset + 4])

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        if not 1 <= self.count <= 0x07B:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        rc = await set_values(
            self.dev_id, self.function_code, self.address, self.registers
        )
        if rc:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        self.is_request = False
        return self


class PDUmaskWriteRegister(ModbusPdu):
    """MaskWriteRegister."""

    function_code = 0x16

    def __init__(
        self,
        *args,
        and_mask: int = 0xFFFF,
        or_mask: int = 0x0000,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.and_mask = and_mask
        self.or_mask = or_mask

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 10

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return struct.pack(">HHH", self.address, self.and_mask, self.or_mask)

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        self.address, self.and_mask, self.or_mask = struct.unpack(
            ">HHH", data[offset : offset + 6]
        )

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        if not 0x0000 <= self.and_mask <= 0xFFFF:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        if not 0x0000 <= self.or_mask <= 0xFFFF:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        if not 1 <= self.count <= 0x07B:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        if values := await get_values(self.dev_id, self.function_code, self.address, 1):
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        rc = await set_values(
            self.dev_id, self.function_code, self.address, cast(list[int], [values])
        )
        if rc:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        self.is_request = False
        return self


DecodePDU.add_pdu(PDUreadHoldingRegisters)
DecodePDU.add_pdu(PDUreadInputRegisters)
DecodePDU.add_pdu(PDUwriteMultipleRegisters)
DecodePDU.add_pdu(PDUwriteSingleRegister)
DecodePDU.add_pdu(PDUreadWriteMultipleRegisters)
DecodePDU.add_pdu(PDUmaskWriteRegister)
