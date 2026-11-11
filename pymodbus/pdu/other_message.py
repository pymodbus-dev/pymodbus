"""Diagnostic record read/write."""

from __future__ import annotations

import struct
from copy import deepcopy
from dataclasses import dataclass

from ..constants import ModbusStatus
from ..exceptions import ModbusException, ModbusIOException
from .device import DeviceInformationFactory, ModbusControlBlock
from .pdu import DecodePDU, ModbusPdu, StoreGet, StoreSet


_MCB = ModbusControlBlock()


class PDUreadExceptionStatus(ModbusPdu):
    """ReadExceptionStatus."""

    function_code = 0x07

    def __init__(
        self,
        *args,
        status: int = 0,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.status: int = status or 0

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", status={self.status}"

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 2 if self.is_request else 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return (
            self.preamble() + b""
            if self.is_request
            else self.preamble() + struct.pack(">B", self.status)
        )

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if not self.is_request:
            self.status = int(data[2])

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Update internal data."""
        self.status = _MCB.Counter.summary()
        self.is_request = False
        return self


class PDUgetCommEventCounter(ModbusPdu):
    """GetCommEventCounter."""

    function_code = 0x0B

    def __init__(
        self,
        *args,
        status: int = 0,
        count: int = 0,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.status: int = status or True
        self.count: int = count

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", count={self.count}, status={self.status}"

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 2 if self.is_request else 6

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return self.preamble() + b""
        ready = ModbusStatus.READY if self.status else ModbusStatus.WAITING
        return self.preamble() + struct.pack(">HH", ready, self.count)

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if not self.is_request:
            ready, self.count = struct.unpack(">HH", data[2:6])
            self.status = ready == ModbusStatus.READY

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Update internal data."""
        self.count = _MCB.Counter.Event
        self.is_request = False
        return self


class PDUgetCommEventLog(ModbusPdu):
    """GetCommEventLog."""

    function_code = 0x0C

    def __init__(
        self,
        *args,
        status: bool = True,
        message_count: int = 0,
        event_count: int = 0,
        events: list[int] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.status = status
        self.message_count = message_count
        self.event_count = event_count
        self.events = events or []

    def __str__(self) -> str:
        """Build representation of pdu."""
        return (
            super().__str__()
            + f", status={self.status}, message_count={self.message_count}"
            + f", event_count={self.event_count}, events={self.events}"
        )

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 2 if self.is_request else int(data[2]) + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return self.preamble() + b""
        ready = ModbusStatus.READY if self.status else ModbusStatus.WAITING
        packet = self.preamble() + struct.pack(">B", 6 + len(self.events))
        packet += struct.pack(">HHH", ready, self.event_count, self.message_count)
        packet += b"".join(struct.pack(">B", e) for e in self.events)
        return packet

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            return
        length = int(data[2]) - 6
        status = struct.unpack(">H", data[3:5])[0]
        self.status = status == ModbusStatus.READY
        self.event_count = struct.unpack(">H", data[5:7])[0]
        self.message_count = struct.unpack(">H", data[7:9])[0]

        self.events = []
        for i in range(9, length + 9):
            self.events.append(int(data[i]))

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Update internal data."""
        self.status = True
        self.message_count = _MCB.Counter.BusMessage
        self.event_count = _MCB.Counter.Event
        self.events = list(_MCB.getEvents())
        return self


ID_ON = 0xFF
ID_OFF = 0x00


class PDUreportDeviceId(ModbusPdu):
    """ReportDeviceId."""

    function_code = 0x11

    def __init__(
        self,
        *args,
        identifier: bytes = b"\x00",
        status: bool = True,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.status = status
        self.identifier = identifier

    def __str__(self) -> str:
        """Build representation of pdu."""
        return (
            super().__str__() + f", status={self.status}, identifier={self.identifier}"
        )

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 2 if self.is_request else int(data[2]) + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return self.preamble() + b""
        status = ID_ON if self.status else ID_OFF
        length = len(self.identifier) + 1
        packet = self.preamble() + struct.pack(">B", length)
        packet += self.identifier  # we assume it is already encoded
        packet += struct.pack(">B", status)
        return packet

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            return None
        byte_count = int(data[2])
        if not 1 <= byte_count <= len(data) - 3:
            return f"byte_count {byte_count} outside 1..{len(data) - 1} "
        self.identifier = data[3 : byte_count + 2]
        status = int(data[-1])
        self.status = status == ID_ON
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Update internal data."""
        information = DeviceInformationFactory.get(_MCB)
        id_data = []
        for v_item in information.values():
            if isinstance(v_item, bytes):
                id_data.append(v_item)
            else:
                id_data.append(v_item.encode())

        identifier = b"-".join(id_data)
        self.identifier = identifier or b"Pymodbus"
        return self


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
        self.records: list[FileRecord] = deepcopy(records) if records else []

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", records={self.records}"

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[2]) + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            packet = self.preamble() + struct.pack("B", len(self.records) * 7)
            for record in self.records:
                packet += struct.pack(
                    ">BHHH",
                    0x06,
                    record.file_number,
                    record.record_number,
                    record.record_length,
                )
        else:
            total = sum(len(record.record_data) + 2 for record in self.records)
            packet = self.preamble() + struct.pack("B", total)
            for record in self.records:
                packet += struct.pack(">BB", len(record.record_data) + 1, 0x06)
                packet += record.record_data
        return packet

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            self.records = []
            if (byte_count := int(data[2])) + 3 != len(data):
                return f"Invalid byte count: {byte_count}"
            for count in range(3, byte_count + 3, 7):
                decoded = struct.unpack(">BHHH", data[count : count + 7])
                record = FileRecord(
                    file_number=decoded[1],
                    record_number=decoded[2],
                    record_length=decoded[3],
                )
                self.records.append(record)
        else:
            count = 1
            self.records.clear()
            byte_count = int(data[2])
            while count < byte_count:
                calc_length, _ = struct.unpack(">BB", data[count + 2 : count + 4])
                count += 2
                record_length = calc_length - 1
                record = FileRecord(
                    record_data=data[count : count + record_length],
                )
                count += record_length
                self.records.append(record)
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
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

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[2]) + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        total_length = sum((record.record_length * 2) + 7 for record in self.records)
        packet = self.preamble() + struct.pack("B", total_length)
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

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        self.records.clear()
        if (byte_count := int(data[2])) + 3 != len(data):
            raise ModbusIOException(f"Invalid byte count: {byte_count}")
        count = 0
        while count < byte_count:
            decoded = struct.unpack(">BHHH", data[count + 3 : count + 10])
            calc_length = decoded[3] * 2
            count += calc_length + 7
            record = FileRecord(
                file_number=decoded[1],
                record_number=decoded[2],
                record_data=data[count - calc_length : count],
            )
            record.record_length = decoded[3]
            self.records.append(record)

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
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
        address: int | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.values: list[int] = values or []
        self.address: int = address or 0

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", address={self.address}, values={self.values}"

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        if self.is_request:
            return 4
        hi_byte = int(data[2])
        lo_byte = int(data[3])
        return ((hi_byte << 8) + lo_byte) + 4

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return self.preamble() + struct.pack(">H", self.address)
        length = len(self.values)
        packet = self.preamble() + struct.pack(">HH", 2 + length * 2, length)
        for value in self.values:
            packet += struct.pack(">H", value)
        return packet

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            self.address = struct.unpack(">H", data[2:])[0]
            return None
        self.values = []
        byte_count, count = struct.unpack(">HH", data[2:6])
        if byte_count + 4 != len(data):
            return f"Illegal bytecount {byte_count}"
        if 6 + count * 2 != len(data):
            return f"Invalid fifo count: {count}"
        for index in range(0, count):
            idx = 6 + index * 2
            self.values.append(struct.unpack(">H", data[idx : idx + 2])[0])
        return None

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get bits from datastore."""
        self.is_request = False
        self.values = [0, 1, 2, 3]  # server dummy response (should be in datastore)
        return self


DecodePDU.add_pdu(PDUreadExceptionStatus)
DecodePDU.add_pdu(PDUgetCommEventCounter)
DecodePDU.add_pdu(PDUgetCommEventLog)
DecodePDU.add_pdu(PDUreportDeviceId)
DecodePDU.add_pdu(PDUreadFileRecord)
DecodePDU.add_pdu(PDUwriteFileRecord)
DecodePDU.add_pdu(PDUreadFifoQueue)
