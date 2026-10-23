"""Diagnostic record read/write."""

from __future__ import annotations

import struct

from ..constants import ModbusStatus
from ..exceptions import ModbusIOException
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

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 8 if is_request else 5

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return b"" if self.is_request else struct.pack(">B", self.status)

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if not self.is_request:
            self.status = int(data[offset + 0])

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Update internal data."""
        self.status = _MCB.Counter.summary()
        self.is_request = False
        return self


class PDUgetCommEventCounter(ModbusPdu):
    """GetCommEventCounter."""

    function_code = 0x0B

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 4 if is_request else 8

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return b""
        ready = ModbusStatus.READY if self.status else ModbusStatus.WAITING
        return struct.pack(">HH", ready, self.count)

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if not self.is_request:
            ready, self.count = struct.unpack(">HH", data[offset : offset + 4])
            self.status = ready == ModbusStatus.READY

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
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

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 4 if is_request else int(data[offset + 2]) + 2 + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return b""
        ready = ModbusStatus.READY if self.status else ModbusStatus.WAITING
        packet = struct.pack(">B", 6 + len(self.events))
        packet += struct.pack(">H", ready)
        packet += struct.pack(">HH", self.event_count, self.message_count)
        packet += b"".join(struct.pack(">B", e) for e in self.events)
        return packet

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            return
        length = int(data[offset])
        status = struct.unpack(">H", data[offset + 1 : offset + 3])[0]
        self.status = status == ModbusStatus.READY
        self.event_count = struct.unpack(">H", data[offset + 3 : offset + 5])[0]
        self.message_count = struct.unpack(">H", data[offset + 5 : offset + 7])[0]

        self.events = []
        for i in range(7, length + 1):
            self.events.append(int(data[offset + i]))

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
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

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 4 if is_request else int(data[offset + 2]) + 2 + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return b""
        status = ID_ON if self.status else ID_OFF
        length = len(self.identifier) + 1
        packet = struct.pack(">B", length)
        packet += self.identifier  # we assume it is already encoded
        packet += struct.pack(">B", status)
        return packet

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            return

        byte_count = int(data[offset])
        if not 1 <= byte_count <= len(data) - 1 - offset:
            raise ModbusIOException(
                f"byte_count {byte_count} outside 1..{len(data) - 1 - offset} "
                f"for packet of length {len(data)}",
                function_code=self.function_code,
            )
        self.identifier = data[offset + 1 : offset + byte_count]
        status = int(data[offset + byte_count])
        self.status = status == ID_ON

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
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


DecodePDU.add_pdu(PDUreadExceptionStatus)
DecodePDU.add_pdu(PDUgetCommEventCounter)
DecodePDU.add_pdu(PDUgetCommEventLog)
DecodePDU.add_pdu(PDUreportDeviceId)
