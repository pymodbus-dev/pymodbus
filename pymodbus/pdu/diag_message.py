"""Diagnostic Record Read/Write."""

from __future__ import annotations

import struct
from typing import Any

from ..constants import CLEAR_STATISTICS, DeviceInformation, ExcCodes, MoreData
from .device import DeviceInformationFactory, ModbusControlBlock
from .pdu import DecodePDU, ModbusPdu, PDUexception, StoreGet, StoreSet, pack_bitstring


_MCB = ModbusControlBlock()


class PDUdiagnostic(ModbusPdu):
    """Diagnostic base."""

    function_code = 0x08

    def __init__(
        self,
        *args,
        message: bytes | int | list | tuple | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        if isinstance(message, int):
            self.message = message.to_bytes(2, "big")
        elif isinstance(message, (list, tuple)):
            packet = b""
            for piece in message:
                packet += struct.pack(">H", piece)
            self.message = packet
        else:
            self.message = message or b"\x00\x00"

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", message={self.message}"

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 6

    @classmethod
    def decode_sub_function_code(cls, data: bytes) -> int:
        """Decode sub function code."""
        return int.from_bytes(data[2:4], "big")

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return (
            self.preamble() + struct.pack(">H", self.sub_function_code) + self.message
        )

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        (self.sub_function_code,) = struct.unpack(">H", data[2:4])
        self.message = data[4:]

    def sub_build_response(self) -> None:
        """get/set info in _MCB."""
        return

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
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
        char = self.message[0]
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

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        size_data = 111 if len(data) > 7 else 0
        return 6 + size_data

    def sub_build_response(self) -> None:
        """Get/set info in _MCB."""
        if self.message == CLEAR_STATISTICS:
            _MCB.Plus.reset()
        else:
            packet = b""
            for piece in _MCB.Plus.encode():
                packet += struct.pack(">H", piece)
            self.message = packet

    def to_bytes(self):
        """Encode a diagnostic response."""
        return (
            self.preamble() + struct.pack(">H", self.sub_function_code) + self.message
        )


class _OutOfSpaceException(Exception):
    """Internal out of space exception."""

    # This exception exists here as a simple, local way to manage response
    # length control for the only MODBUS command which requires it under
    # standard, non-error conditions.
    #
    # See Page 5/50 of MODBUS Application Protocol Specification V1.1b3.

    def __init__(self, oid: int) -> None:
        self.oid = oid
        super().__init__()
        self.oid = oid


class PDUreadDeviceInformation(ModbusPdu):
    """Base PDU for dispatching Encapsulated Interface Transport messages."""

    function_code = 0x2B
    sub_function_code = 0x0E

    def __init__(
        self,
        *args,
        read_code: int | None = None,
        object_id: int = 0,
        information: dict[int, Any] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)
        self.read_code = read_code or int(DeviceInformation.BASIC)
        self.object_id = object_id
        self.information: dict[int, Any] = information or {}
        self.number_of_objects = 0
        self.conformity = 0x83  # I support everything right now
        self.next_object_id = 0x00
        self.more_follows = MoreData.NOTHING
        self.space_left = 253 - 6

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + (
            ",  "
            + f"read_code={self.read_code}, "
            + f"object_id={self.object_id}, "
            + f"information={self.information}, "
            + f"number_of_objects={self.number_of_objects}, "
            + f"conformity={self.conformity}, "
            + f"next_object_id={self.next_object_id}, "
            + f"more_follows={self.more_follows}, "
            + f"space_left={self.space_left}, "
        )

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        data_len = len(data)
        if self.is_request:
            if data_len != 5:
                return 999
            return 5
        size = 8  # skip the header information
        if data_len < size:
            return 999
        count = int(data[7])

        while count > 0:
            if data_len < size + 2:
                return 998
            _, object_length = struct.unpack(">BB", data[size : size + 2])
            size += object_length + 2
            count -= 1
        return size

    @classmethod
    def decode_sub_function_code(cls, data: bytes) -> int:
        """Decode sub function code."""
        return int(data[2])

    def _encode_object(self, object_id: int, data: str | bytes | ModbusPdu) -> bytes:
        """Encode object."""
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, bytes):
            data = data.to_bytes()
        data_len = len(data)
        self.space_left -= 2 + data_len
        if self.space_left <= 0:
            raise _OutOfSpaceException(object_id)
        encoded_obj = struct.pack(">BB", object_id, data_len)
        encoded_obj += data
        self.number_of_objects += 1
        return encoded_obj

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            packet = self.preamble() + struct.pack(
                ">BBB", self.sub_function_code, self.read_code, self.object_id
            )
            return packet
        packet = self.preamble() + struct.pack(
            ">BBB", self.sub_function_code, self.read_code, self.conformity
        )
        objects = b""
        try:
            for object_id, data in iter(self.information.items()):
                if isinstance(data, list):
                    for item in data:
                        objects += self._encode_object(object_id, item)
                else:
                    objects += self._encode_object(object_id, data)
        except _OutOfSpaceException as exc:
            self.next_object_id = exc.oid
            self.more_follows = MoreData.KEEP_READING

        packet += struct.pack(
            ">BBB", self.more_follows, self.next_object_id, self.number_of_objects
        )
        packet += objects
        return packet

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        if self.is_request:
            self.read_code, self.object_id = struct.unpack(">BB", data[3:5])
            return
        (
            self.read_code,
            self.conformity,
            self.more_follows,
            self.next_object_id,
            self.number_of_objects,
        ) = struct.unpack(">BBBBB", data[3:8])
        self.information.clear()
        count = 8  # skip the header information
        while count < len(data):
            object_id, object_length = struct.unpack(">BB", data[count : count + 2])
            count += object_length + 2
            if object_id not in self.information:
                self.information[object_id] = data[count - object_length : count]
            elif isinstance(self.information[object_id], list):
                self.information[object_id].append(data[count - object_length : count])
            else:
                self.information[object_id] = [
                    self.information[object_id],
                    data[count - object_length : count],
                ]

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Update diagnostic request on the given device."""
        if not 0x00 <= self.object_id <= 0xFF:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        if not 0x00 <= self.read_code <= 0x04:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)

        self.information = DeviceInformationFactory.get(
            _MCB, self.read_code, self.object_id
        )
        if self.read_code == DeviceInformation.SPECIFIC and (
            0x07 <= self.object_id < 0x80 or not self.information.get(self.object_id)
        ):
            return PDUexception(
                self.dev_id, self.function_code, ExcCodes.ILLEGAL_ADDRESS
            )
        self.is_request = False
        return self


DecodePDU.add_pdu(PDUdiagnostic)
DecodePDU.add_pdu(PDUreturnQueryData)
DecodePDU.add_pdu(PDUrestartCommunicationsOption)
DecodePDU.add_pdu(PDUreturnDiagnosticRegister)
DecodePDU.add_pdu(PDUchangeAsciiInputDelimiter)
DecodePDU.add_pdu(PDUforceListenOnlyMode)
DecodePDU.add_pdu(PDUclearCounters)
DecodePDU.add_pdu(PDUreturnBusMessageCount)
DecodePDU.add_pdu(PDUreturnBusCommunicationErrorCount)
DecodePDU.add_pdu(PDUreturnBusExceptionErrorCount)
DecodePDU.add_pdu(PDUreturnDeviceMessageCount)
DecodePDU.add_pdu(PDUreturnDeviceNoResponseCount)
DecodePDU.add_pdu(PDUreturnDeviceNAKCount)
DecodePDU.add_pdu(PDUreturnDeviceBusyCount)
DecodePDU.add_pdu(PDUreturnDeviceBusCharacterOverrunCount)
DecodePDU.add_pdu(PDUreturnIopOverrunCount)
DecodePDU.add_pdu(PDUclearOverrunCount)
DecodePDU.add_pdu(PDUgetClearModbusPlus)
DecodePDU.add_pdu(PDUreadDeviceInformation)
