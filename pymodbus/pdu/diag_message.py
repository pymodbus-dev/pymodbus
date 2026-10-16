"""Diagnostic Record Read/Write."""

from __future__ import annotations

import struct
from typing import cast

from ..constants import ModbusPlusOperation
from .device import ModbusControlBlock
from .pdu import DecodePDU, ModbusPdu, StoreGet, StoreSet
from .utils import pack_bitstring


_MCB = ModbusControlBlock()


class PDUdiagnostic(ModbusPdu):
    """Diagnostic base."""

    function_code = 0x08

    def __init__(
        self,
        *args,
        message: bytes | int | list | tuple | None = 0,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.message: bytes | int | list | tuple = message or []

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", message={self.message}"

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 8

    @classmethod
    def decode_sub_function_code(cls, offset: int, data: bytes) -> int:
        """Decode sub function code."""
        return int.from_bytes(data[offset + 2 : offset + 4], "big")

    def to_bytes(self) -> bytes:
        """Encode the message."""
        packet = struct.pack(">H", self.sub_function_code)
        if not self.is_request:
            if isinstance(self.message, bytes):
                packet += self.message
                return packet
            if isinstance(self.message, int):
                packet += struct.pack(">H", self.message)
                return packet
            if isinstance(self.message, (list, tuple)):
                for piece in self.message:
                    packet += struct.pack(">H", piece)
                return packet
            raise TypeError(f"UNKNOWN DIAG message type: {type(self.message)}")
        return packet

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        (self.sub_function_code,) = struct.unpack(">H", data[offset : offset + 2])
        data = data[offset + 2 :]
        if self.sub_function_code == PDUreturnQueryData.sub_function_code:
            self.message = data
        elif data_len := len(data):
            if data_len % 2:
                data_len += 1
                data += b"0"
            if (word_len := data_len // 2) == 1:
                (self.message,) = struct.unpack(">H", data[:2])
            else:
                self.message = struct.unpack(">" + "H" * word_len, data[: 2 * word_len])

    def sub_build_response(self) -> None:
        """get/set info in _MCB."""
        return

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Update internal data."""
        self.is_request = False
        self.sub_build_response()
        return self


class PDUreturnQueryData(PDUdiagnostic):
    """ReturnQueryData."""

    sub_function_code = 0x0000


class PDUrestartCommunicationsOption(PDUdiagnostic):
    """RestartCommunicationsOption."""

    sub_function_code = 0x0001


class PDUreturnDiagnosticRegister(PDUdiagnostic):
    """ReturnDiagnosticRegister."""

    sub_function_code = 0x0002

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = pack_bitstring(_MCB.getDiagnosticRegister())


class PDUchangeAsciiInputDelimiter(PDUdiagnostic):
    """ChangeAsciiInputDelimiter."""

    sub_function_code = 0x0003

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        char = (cast(int, self.message) & 0xFF00) >> 8
        _MCB.Delimiter = char


class PDUforceListenOnlyMode(PDUdiagnostic):
    """ForceListenOnlyMode."""

    sub_function_code = 0x0004

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        _MCB.ListenOnly = True


class PDUclearCounters(PDUdiagnostic):
    """ClearCounters."""

    sub_function_code = 0x000A

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        _MCB.reset()


class PDUreturnBusMessageCount(PDUdiagnostic):
    """ReturnBusMessageCount."""

    sub_function_code = 0x000B

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.BusMessage


class PDUreturnBusCommunicationErrorCount(PDUdiagnostic):
    """ReturnBusCommunicationErrorCount."""

    sub_function_code = 0x000C

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.BusCommunicationError


class PDUreturnBusExceptionErrorCount(PDUdiagnostic):
    """ReturnBusExceptionErrorCount."""

    sub_function_code = 0x000D

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.BusExceptionError


class PDUreturnDeviceMessageCount(PDUdiagnostic):
    """ReturnDeviceMessageCount."""

    sub_function_code = 0x000E

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.DeviceMessage


class PDUreturnDeviceNoResponseCount(PDUdiagnostic):
    """ReturnDeviceNoResponseCount."""

    sub_function_code = 0x000F

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.DeviceNoResponse


class PDUreturnDeviceNAKCount(PDUdiagnostic):
    """ReturnDeviceNAKCount."""

    sub_function_code = 0x0010

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.DeviceNAK


class PDUreturnDeviceBusyCount(PDUdiagnostic):
    """ReturnDeviceBusyCount."""

    sub_function_code = 0x0011

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.DEVICE_BUSY


class PDUreturnDeviceBusCharacterOverrunCount(PDUdiagnostic):
    """ReturnDeviceBusCharacterOverrunCount."""

    sub_function_code = 0x0012

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.BusCharacterOverrun


class PDUreturnIopOverrunCount(PDUdiagnostic):
    """ReturnIopOverrunCount."""

    sub_function_code = 0x0013

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        self.message = _MCB.Counter.BusCharacterOverrun


class PDUclearOverrunCount(PDUdiagnostic):
    """ClearOverrunCount."""

    sub_function_code = 0x0014

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        _MCB.Counter.BusCharacterOverrun = 0x0000


class PDUgetClearModbusPlus(PDUdiagnostic):
    """GetClearModbusPlus."""

    sub_function_code = 0x0015

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        if is_request:
            return 8
        size_data = 111 if len(data) > 7 else 0
        return 1 + 2 + 2 + 2 + size_data

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        if self.message == ModbusPlusOperation.CLEAR_STATISTICS:
            _MCB.Plus.reset()
            self.message = ModbusPlusOperation.CLEAR_STATISTICS
        else:
            if not isinstance(self.message, list):
                self.message = [self.message]
            self.message += _MCB.Plus.encode()

    def to_bytes(self):
        """Encode a diagnostic response."""
        packet = struct.pack(">H", self.sub_function_code)
        packet += struct.pack(">H", self.message)
        return packet


DecodePDU.add_pdu(PDUdiagnostic)
DecodePDU.add_pdu(PDUreturnQueryData)
DecodePDU.add_pdu(PDUrestartCommunicationsOption)
DecodePDU.add_pdu(PDUreturnDiagnosticRegister)
DecodePDU.add_pdu(PDUchangeAsciiInputDelimiter)
DecodePDU.add_pdu(PDUforceListenOnlyMode)
DecodePDU.add_pdu(PDUclearCounters)
DecodePDU.add_pdu(PDUreturnBusMessageCount)
DecodePDU.add_pdu(PDUreturnBusCommunicationErrorCount)
DecodePDU.add_pdu(PDUreturnDeviceMessageCount)
DecodePDU.add_pdu(PDUreturnDeviceNoResponseCount)
DecodePDU.add_pdu(PDUreturnDeviceNAKCount)
DecodePDU.add_pdu(PDUreturnDeviceBusyCount)
DecodePDU.add_pdu(PDUreturnDeviceBusCharacterOverrunCount)
DecodePDU.add_pdu(PDUreturnIopOverrunCount)
DecodePDU.add_pdu(PDUclearOverrunCount)
DecodePDU.add_pdu(PDUgetClearModbusPlus)
