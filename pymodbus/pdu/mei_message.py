"""Encapsulated Interface (MEI) Transport Messages."""

from __future__ import annotations

import struct
from typing import Any

from ..constants import DeviceInformation, ExcCodes, MoreData
from .device import DeviceInformationFactory, ModbusControlBlock
from .pdu import DecodePDU, ModbusPdu, PDUexception, StoreGet, StoreSet


_MCB = ModbusControlBlock()


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

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        if is_request:
            return 7
        size = 8  # skip the header information
        if (data_len := len(data) - offset) < size:
            return 999
        count = int(data[offset + 7])

        while count > 0:
            if data_len < size + 2:
                return 998
            _, object_length = struct.unpack(
                ">BB", data[offset + size : offset + size + 2]
            )
            size += object_length + 2
            count -= 1
        return size + 2

    @classmethod
    def decode_sub_function_code(cls, offset: int, data: bytes) -> int:
        """Decode sub function code."""
        return int.from_bytes(data[offset + 2 : offset + 3])

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
            packet = struct.pack(
                ">BBB", self.sub_function_code, self.read_code, self.object_id
            )
            return packet
        packet = struct.pack(
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

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            self.sub_function_code, self.read_code, self.object_id = struct.unpack(
                ">BBB", data[offset : offset + 3]
            )
            return
        (
            self.sub_function_code,
            self.read_code,
            self.conformity,
            self.more_follows,
            self.next_object_id,
            self.number_of_objects,
        ) = struct.unpack(">BBBBBB", data[offset + 0 : offset + 6])
        count = 6  # skip the header information
        self.information.clear()

        while count < len(data) - offset:
            object_id, object_length = struct.unpack(
                ">BB", data[offset + count : offset + count + 2]
            )
            count += object_length + 2
            if object_id not in self.information:
                self.information[object_id] = data[
                    offset + count - object_length : offset + count
                ]
            elif isinstance(self.information[object_id], list):
                self.information[object_id].append(
                    data[offset + count - object_length : offset + count]
                )
            else:
                self.information[object_id] = [
                    self.information[object_id],
                    data[count - object_length : count],
                ]

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Update diagnostic request on the given device."""
        if not 0x00 <= self.object_id <= 0xFF:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        if not 0x00 <= self.read_code <= 0x04:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)

        information = DeviceInformationFactory.get(_MCB, self.read_code, self.object_id)
        if self.read_code == DeviceInformation.SPECIFIC and (
            0x07 <= self.object_id < 0x80 or not information.get(self.object_id)
        ):
            return PDUexception(
                self.dev_id, self.function_code, ExcCodes.ILLEGAL_ADDRESS
            )
        self.is_request = False
        return self


DecodePDU.add_pdu(PDUreadDeviceInformation)
