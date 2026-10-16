"""File Record Read/Write Messages."""

from __future__ import annotations

import struct
from dataclasses import dataclass

from ..exceptions import ModbusException, ModbusIOException
from .pdu import DecodePDU, ModbusPdu, StoreGet, StoreSet


@dataclass
class FileRecord:
    """Represents a file record and its relevant data."""

    file_number: int = 0
    record_number: int = 0
    record_data: bytes = b""
    record_length: int = 0

    def __post_init__(self) -> None:
        """Initialize a new instance."""
        if self.record_data:
            if self.record_length:
                raise ModbusException("Use either record_data= or record_length=")
            self.record_length = len(self.record_data)
        if self.record_length % 2:
            raise ModbusException("length of record_data must be a multiple of 2")
        self.record_length //= 2


class PDUreadFileRecord(ModbusPdu):
    """ReadFileRecord."""

    function_code = 0x14

    def __init__(
        self,
        *args,
        records: list[FileRecord] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.records: list[FileRecord] = records or []

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", records={self.records}"

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[offset + 2]) + 2 + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            packet = struct.pack("B", len(self.records) * 7)
            for record in self.records:
                packet += struct.pack(
                    ">BHHH",
                    0x06,
                    record.file_number,
                    record.record_number,
                    record.record_length,
                )
        else:
            total = sum(len(record.record_data) + 1 + 1 for record in self.records)
            packet = struct.pack("B", total)
            for record in self.records:
                packet += struct.pack(">BB", len(record.record_data) + 1, 0x06)
                packet += record.record_data
        return packet

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            self.records = []
            if (byte_count := int(data[offset + 0])) > len(data) - 1 - offset:
                raise ModbusIOException(f"Invalid byte count: {byte_count}")
            for count in range(1, byte_count, 7):
                decoded = struct.unpack(
                    ">BHHH", data[count + offset : count + 7 + offset]
                )
                record = FileRecord(
                    file_number=decoded[1],
                    record_number=decoded[2],
                    record_length=decoded[3],
                )
                self.records.append(record)
        else:
            count = 1
            self.records.clear()
            byte_count = int(data[offset + 0])
            while count < byte_count:
                calc_length, _ = struct.unpack(
                    ">BB", data[count + offset : count + 2 + offset]
                )
                count += 2

                record_length = (
                    calc_length - 1
                )  # response length includes the type byte
                record = FileRecord(
                    record_data=data[count + offset : count + record_length + offset],
                )
                count += record_length
                self.records.append(record)

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        for record in self.records:
            record.record_data = b"SERVER DUMMY RECORD."
            record.record_length = len(record.record_data) // 2
        self.is_request = False
        return self


class PDUwriteFileRecord(ModbusPdu):
    """WriteFileRecord."""

    function_code = 0x15

    def __init__(
        self,
        *args,
        records: list[FileRecord] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.records: list[FileRecord] = records or []

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", records={self.records}"

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[offset + 2]) + 2 + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        total_length = sum((record.record_length * 2) + 7 for record in self.records)
        packet = struct.pack("B", total_length)
        for record in self.records:
            packet += struct.pack(
                ">BHHH",
                0x06,
                record.file_number,
                record.record_number,
                record.record_length,
            )
            packet += record.record_data
        return packet

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        count = 1
        self.records.clear()
        if (byte_count := int(data[offset + 0])) > len(data) - 1 - offset:
            raise ModbusIOException(f"Invalid byte count: {byte_count}")
        while count < byte_count:
            decoded = struct.unpack(">BHHH", data[count + offset : count + 7 + offset])
            calc_length = decoded[3] * 2
            count += calc_length + 7
            record = FileRecord(
                file_number=decoded[1],
                record_number=decoded[2],
                record_data=data[count - calc_length : count],
            )
            record.record_length = decoded[3]
            self.records.append(record)

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        self.is_request = False
        return self


class PDUreadFifoQueue(ModbusPdu):
    """ReadFifoQueue."""

    function_code = 0x18

    def __init__(
        self,
        *args,
        values: list[int] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.values: list[int] = values or []

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", values={self.values}"

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        if is_request:
            return 6
        hi_byte = int(data[offset + 2])
        lo_byte = int(data[offset + 3])
        return ((hi_byte << 8) + lo_byte) + 4

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return struct.pack(">H", self.address)
        length = len(self.values)
        packet = struct.pack(">HH", 2 + length * 2, length)
        for value in self.values:
            packet += struct.pack(">H", value)
        return packet

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            self.address = struct.unpack(">H", data[offset : offset + 2])[0]
        self.values = []
        _, count = struct.unpack(">HH", data[offset + 0 : offset + 4])
        if 4 + count * 2 > len(data) - offset:
            raise ModbusIOException(f"Invalid fifo count: {count}")
        for index in range(0, count):
            idx = 4 + index * 2
            self.values.append(
                struct.unpack(">H", data[offset + idx : offset + idx + 2])[0]
            )

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        self.is_request = False
        self.values = [0, 1, 2, 3]  # server dummy response (should be in datastore)
        return self


DecodePDU.add_pdu(PDUreadFileRecord)
DecodePDU.add_pdu(PDUwriteFileRecord)
DecodePDU.add_pdu(PDUreadFifoQueue)
