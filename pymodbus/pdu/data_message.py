"""Bit Reading Request/Response messages."""

import struct
from collections.abc import Sequence
from copy import copy
from typing import cast

from ..constants import ExcCodes, ModbusStatus
from .pdu import (
    DecodePDU,
    ModbusPdu,
    StoreGet,
    StoreSet,
    pack_bitstring,
    unpack_bitstring,
)


class PDUreadCoils(ModbusPdu):
    """ReadCoils."""

    function_code = 1
    MAX_COUNT = 2000

    def __init__(
        self,
        *args,
        address: int | None = None,
        count: int | None = None,
        bits: Sequence[bool] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        if bits and not count:
            count = len(bits)
        self.address: int = address if address is not None else -1
        self.count: int = count if count is not None else -1
        self.bits = copy(bits) or []
        super().__init__(*args, **kwargs)

    def verify(self) -> str | None:
        """Verify params."""
        if not 0 <= self.count <= self.MAX_COUNT:
            return f"Invalid count({self.count})"
        if self.is_request and not 0 <= self.address <= 65535:
            return f"Invalid address({self.address})"
        return None

    def __str__(self) -> str:
        """Build representation of pdu."""
        return (
            super().__str__()
            + f"address={self.address}, count={self.count}, bits={self.bits}"
        )

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 6 if self.is_request else int(data[2]) + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if text := self.verify():
            self.raiseExp(text)
        if self.is_request:
            return self.preamble() + struct.pack(">HH", self.address, self.count)
        result = pack_bitstring(self.bits)
        return self.preamble() + struct.pack(">B", len(result)) + result

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count = struct.unpack(">HH", data[2:6])
        else:
            byte_count = int(data[2])
            self.bits = unpack_bitstring(data[3:])
            self.count = len(self.bits)
            if self.count != byte_count * 8:
                return (
                    f"byte_count({byte_count}) * 8 not identical to count({self.count})"
                )
        if text := self.verify():
            return text
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get bits from datastore."""
        values = await v_get(self.dev_id, self.function_code, self.address, self.count)
        if isinstance(values, ExcCodes):
            return self.respondExp(values)
        self.is_request = False
        self.bits = cast(list[bool], values)
        return self


class PDUreadDiscreteInputs(PDUreadCoils):
    """ReadDiscreteInputsRequest."""

    function_code = 2


class PDUwriteSingleCoil(PDUreadCoils):
    """WriteSingleCoil."""

    function_code = 5

    def verify(self) -> str | None:
        """Verify params."""
        if text := super().verify():
            return text
        if self.count != 1:
            return f"Invalid count({self.count})"
        if len(self.bits) != 1:
            return f"Invalid bits({self.bits})"
        return None

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 6

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if text := self.verify():
            self.raiseExp(text)
        val = ModbusStatus.ON if self.bits[0] else ModbusStatus.OFF
        return super().preamble() + struct.pack(">HH", self.address, val)

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        self.address, value = struct.unpack(">HH", data[2:])
        self.bits = (
            [bool(value)] if value in (ModbusStatus.ON, ModbusStatus.OFF) else []
        )
        self.count = len(self.bits)
        if text := self.verify():
            return text
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get bits from datastore."""
        if rc := await v_set(self.dev_id, self.function_code, self.address, self.bits):
            return self.respondExp(rc)
        values = await v_get(self.dev_id, self.function_code, self.address, self.count)
        if isinstance(values, ExcCodes):
            return self.respondExp(values)
        self.is_request = False
        self.bits = cast(list[bool], values)
        return self


class PDUwriteMultipleCoils(PDUreadCoils):
    """WriteMultipleCoils."""

    function_code = 15
    MAX_COUNT = 1965

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[6]) + 7 if self.is_request else 6

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            byte_count = (self.count + 7) // 8
            return (
                self.preamble()
                + struct.pack(
                    ">HHB",
                    self.address,
                    self.count,
                    byte_count,
                )
                + pack_bitstring(self.bits)
            )
        return self.preamble() + struct.pack(">HH", self.address, self.count)

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count, byte_count = struct.unpack(">HHB", data[2:7])
            self.bits = unpack_bitstring(data[7:])
            if self.count != byte_count * 8:
                return (
                    f"byte_count({byte_count}) * 8 not identical to count({self.count})"
                )
        else:
            self.address, self.count = struct.unpack(">HH", data[2:])
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get bits from datastore."""
        if rc := await v_set(self.dev_id, self.function_code, self.address, self.bits):
            return self.respondExp(rc)
        values = await v_get(self.dev_id, self.function_code, self.address, self.count)
        if isinstance(values, ExcCodes):
            return self.respondExp(values)
        self.is_request = False
        self.bits = cast(list[bool], values)
        return self


class PDUreadHoldingRegisters(ModbusPdu):
    """ReadHoldingRegisters."""

    function_code = 3
    MAX_COUNT = 125

    def __init__(
        self,
        *args,
        address: int | None = None,
        count: int | None = None,
        registers: Sequence[int] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        if registers and not count:
            count = len(registers)
        self.address: int = address if address is not None else -1
        self.count: int = count if count is not None else -1
        self.registers = copy(registers) or []
        super().__init__(*args, **kwargs)

    def verify(self) -> str | None:
        """Verify params."""
        if not 0 <= self.count <= self.MAX_COUNT:
            return f"Invalid count({self.count})"
        if self.is_request and not 0 <= self.address <= 65535:
            return f"Invalid address({self.address})"
        return None

    def __str__(self) -> str:
        """Build representation of pdu."""
        return (
            super().__str__()
            + f"address={self.address}, count={self.count}, registers={self.registers}"
        )

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 6 if self.is_request else int(data[2]) + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if text := self.verify():
            self.raiseExp(text)
        if self.is_request:
            return self.preamble() + struct.pack(">HH", self.address, self.count)
        result = struct.pack(">B", len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack(">H", register)
        return self.preamble() + result

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count = struct.unpack(">HH", data[2:])
        else:
            if (byte_count := int(data[2])) + 3 != (x := len(data)):
                return f"byte_count {byte_count} > length of packet {x}"
            self.registers = []
            for i in range(3, byte_count + 3, 2):
                self.registers.append(struct.unpack(">H", data[i : i + 2])[0])
            self.count = len(self.registers)
        if text := self.verify():
            return text
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get bits from datastore."""
        values = await v_get(self.dev_id, self.function_code, self.address, self.count)
        if isinstance(values, ExcCodes):
            return self.respondExp(values)
        self.is_request = False
        self.registers = cast(list[int], values)
        return self


class PDUreadInputRegisters(PDUreadHoldingRegisters):
    """ReadInputRegisters."""

    function_code = 4


class PDUwriteSingleRegister(PDUreadHoldingRegisters):
    """WriteSingleRegister."""

    function_code = 6
    MAX_COUNT = 1

    def verify(self) -> str | None:
        """Verify params."""
        if text := super().verify():
            return text
        if len(self.registers) != 1:
            return f"Invalid registers({self.registers})"
        return None

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 6

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if text := self.verify():
            self.raiseExp(text)
        return self.preamble() + struct.pack(">HH", self.address, self.registers[0])

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        self.address, register = struct.unpack(">HH", data[2:])
        self.registers = [register]
        self.count = len(self.registers)
        if text := self.verify():
            return text
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get registers from datastore."""
        if rc := await v_set(
            self.dev_id, self.function_code, self.address, self.registers
        ):
            return self.respondExp(rc)

        registers = await v_get(self.dev_id, self.function_code, self.address, 1)
        if isinstance(registers, ExcCodes):
            return self.respondExp(registers)
        self.is_request = False
        self.registers = cast(list[int], registers)
        return self


class PDUwriteMultipleRegisters(PDUreadHoldingRegisters):
    """WriteMultipleRegisters."""

    function_code = 16
    MAX_COUNT = 123

    def verify(self) -> str | None:
        """Verify params."""
        if text := super().verify():
            return text
        if self.is_request and len(self.registers) != self.count:
            return f"Invalid registers({self.registers})"
        return None

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[6]) + 7 if self.is_request else 6

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if text := self.verify():
            self.raiseExp(text)
        if self.is_request:
            packet = struct.pack(">HHB", self.address, self.count, self.count * 2)
            for value in self.registers:
                packet += struct.pack(">H", value)
            return self.preamble() + packet
        return self.preamble() + struct.pack(">HH", self.address, self.count)

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count, byte_count = struct.unpack(">HHB", data[2:7])
            self.registers = [
                struct.unpack(">H", data[idx : idx + 2])[0]
                for idx in range(7, byte_count + 7, 2)
            ]
            self.count = len(self.registers)
            if self.count != byte_count * 8:
                return (
                    f"byte_count({byte_count}) * 8 not identical to count({self.count})"
                )
        else:
            self.address, self.count = struct.unpack(">HH", data[2:])
        if text := self.verify():
            return text
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get bits from datastore."""
        if rc := await v_set(
            self.dev_id, self.function_code, self.address, self.registers
        ):
            return self.respondExp(rc)
        self.is_request = False
        return self


class PDUreadWriteMultipleRegisters(PDUreadHoldingRegisters):
    """ReadWriteMultipleRegisters."""

    function_code = 23
    MAX_COUNT = 125
    MAX_WRITE_COUNT = 121

    def __init__(
        self,
        *args,
        write_address: int | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        self.write_address: int = write_address if write_address is not None else -1
        super().__init__(*args, **kwargs)

    def verify(self) -> str | None:
        """Verify params."""
        if text := super().verify():
            return text
        if not 0 <= (x := len(self.registers)) <= self.MAX_WRITE_COUNT:
            return f"Invalid write count({x})"
        if self.is_request and not 0 <= self.write_address <= 65535:
            return f"Invalid write_address({self.write_address})"
        return None

    def __str__(self) -> str:
        """Build representation of pdu."""
        return (
            super().__str__()
            + f"address={self.address}, count={self.count}, write_address={self.write_address}, registers={self.registers}"
        )

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[10]) + 11 if self.is_request else int(data[2]) + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        reg_len = len(self.registers)
        reg_to_bytes = b""
        for register in self.registers:
            reg_to_bytes += struct.pack(">H", register)
        if self.is_request:
            return (
                self.preamble()
                + struct.pack(
                    ">HHHHB",
                    self.address,
                    self.count,
                    self.write_address,
                    reg_len,
                    reg_len * 2,
                )
                + reg_to_bytes
            )
        return self.preamble() + struct.pack(">B", reg_len * 2) + reg_to_bytes

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            (self.address, self.count, self.write_address, write_count, byte_count) = (
                struct.unpack(">HHHHB", data[2:11])
            )
            if byte_count + 11 != (x := len(data)):
                return f"byte_count {byte_count} > length of packet {x}"
            if byte_count != write_count * 2:
                return f"byte_count {byte_count} * 2 not identical to {write_count}"
            self.registers = [
                struct.unpack(">H", data[i : i + 2])[0]
                for i in range(11, byte_count + 11, 2)
            ]
            if write_count != (x := len(self.registers)):
                return f"write_count {write_count} not identical to number of registers {x}"
        else:
            if (byte_count := int(data[2])) + 3 != (x := len(data)):
                return f"byte_count {byte_count} > length of packet {x}"
            self.registers = []
            for i in range(3, byte_count + 3, 2):
                self.registers.append(struct.unpack(">H", data[i : i + 2])[0])
            self.count = len(self.registers)
        if text := self.verify():
            return text
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get bits from datastore."""
        rc = await v_set(
            self.dev_id, self.function_code, self.write_address, self.registers
        )
        if rc:
            return self.respondExp(rc)
        values = await v_get(self.dev_id, self.function_code, self.address, self.count)
        if isinstance(values, ExcCodes):
            return self.respondExp(values)
        self.is_request = False
        self.registers = cast(list[int], values)
        return self


class PDUmaskWriteRegister(PDUreadHoldingRegisters):
    """MaskWriteRegister."""

    function_code = 0x16
    MAX_COUNT = 123

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

    def verify(self) -> str | None:
        """Verify params."""
        if text := super().verify():
            return text
        if not 0x0000 <= self.and_mask <= 0xFFFF:
            return "Illegal and_mask"
        if not 0x0000 <= self.or_mask <= 0xFFFF:
            return "Illegal or_mask"
        return None

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", and_mask={self.and_mask}, or_mask={self.or_mask}"

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 8

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return self.preamble() + struct.pack(
            ">HHH", self.address, self.and_mask, self.or_mask
        )

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        self.address, self.and_mask, self.or_mask = struct.unpack(">HHH", data[2:8])
        if text := self.verify():
            return text
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get bits from datastore."""
        values = await v_get(self.dev_id, self.function_code, self.address, self.count)
        if isinstance(values, ExcCodes):
            return self.respondExp(values)
        values = (cast(Sequence[int], values)[0] & self.and_mask) | (
            self.or_mask & ~self.and_mask
        )
        if rc := await v_set(
            self.dev_id, self.function_code, self.address, self.registers
        ):
            return self.respondExp(rc)
        self.is_request = False
        return self


DecodePDU.add_pdu(PDUreadCoils)
DecodePDU.add_pdu(PDUreadDiscreteInputs)
DecodePDU.add_pdu(PDUwriteSingleCoil)
DecodePDU.add_pdu(PDUwriteMultipleCoils)
DecodePDU.add_pdu(PDUreadHoldingRegisters)
DecodePDU.add_pdu(PDUreadInputRegisters)
DecodePDU.add_pdu(PDUwriteMultipleRegisters)
DecodePDU.add_pdu(PDUwriteSingleRegister)
DecodePDU.add_pdu(PDUreadWriteMultipleRegisters)
DecodePDU.add_pdu(PDUmaskWriteRegister)
