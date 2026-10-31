"""Bit Reading Request/Response messages."""

import struct
from collections.abc import Sequence
from typing import cast

from ..constants import ExcCodes, ModbusStatus
from ..exceptions import ModbusIOException
from .pdu import DecodePDU, ModbusPdu, PDUexception, StoreGet, StoreSet
from .utils import pack_bitstring, unpack_bitstring


class PDUreadCoils(ModbusPdu):
    """ReadCoils."""

    function_code = 1
    MAX_COUNT = 2000

    def __init__(
        self,
        *args,
        bits: Sequence[bool] | None = None,
        **kwargs,
    ) -> None:
        """Initialize."""
        if bits:
            kwargs |= {"count": kwargs.get("count", len(bits))}
        super().__init__(*args, **kwargs)
        self.bits = bits or []

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", bits={self.bits}"

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 8 if is_request else int(data[offset + 2]) + 2 + 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            return struct.pack(">HH", self.address, self.count)
        result = pack_bitstring(self.bits)
        return struct.pack(">B", len(result)) + result

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count = struct.unpack(">HH", data[offset : offset + 4])
        else:
            self.bits = unpack_bitstring(data[offset + 1 :])
            self.count = len(self.bits)

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
        self.bits = cast(list[bool], values)
        return self


class PDUreadDiscreteInputs(PDUreadCoils):
    """ReadDiscreteInputsRequest."""

    function_code = 2


class PDUwriteSingleCoil(PDUreadCoils):
    """WriteSingleCoil."""

    function_code = 5

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 8

    def to_bytes(self) -> bytes:
        """Encode the message."""
        val = ModbusStatus.ON if self.bits[0] else ModbusStatus.OFF
        return struct.pack(">HH", self.address, val)

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        self.address, value = struct.unpack(">HH", data[offset : offset + 4])
        if value in (ModbusStatus.ON, ModbusStatus.OFF):
            self.bits = [bool(value)]
        else:
            self.bits = [bool(value)]
        
        self.bits = [bool(value)]
        self.count = 1

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        if not self.bits:
            return PDUexception(self.dev_id, self.function_code, ExcCodes.ILLEGAL_VALUE)
        if rc := await set_values(
            self.dev_id, self.function_code, self.address, self.bits
        ):
            return PDUexception(self.dev_id, self.function_code, rc)

        values = await get_values(
            self.dev_id, self.function_code, self.address, self.count
        )
        if isinstance(values, ExcCodes):
            return PDUexception(self.dev_id, self.function_code, values)
        self.is_request = False
        self.bits = cast(list[bool], values)
        return self


class PDUwriteMultipleCoils(PDUreadCoils):
    """WriteMultipleCoils."""

    function_code = 15
    MAX_COUNT = 2000

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return int(data[offset + 6]) + 6 + 3 if is_request else 8

    def to_bytes(self) -> bytes:
        """Encode the message."""
        if self.is_request:
            byte_count = (self.count + 7) // 8
            return struct.pack(
                ">HHB", self.address, self.count, byte_count
            ) + pack_bitstring(self.bits)
        return struct.pack(">HH", self.address, self.count)

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        if self.is_request:
            self.address, self.count, byte_count = struct.unpack(
                ">HHB", data[offset : offset + 5]
            )
            self.bits = unpack_bitstring(
                data[offset + 5 : offset + 5 + cast(int, byte_count)]
            )[: self.count]
        else:
            self.address, self.count = struct.unpack(">HH", data[offset : offset + 4])

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get bits from datastore."""
        if rc := await set_values(
            self.dev_id, self.function_code, self.address, self.bits
        ):
            return PDUexception(self.dev_id, self.function_code, rc)
        values = await get_values(
            self.dev_id, self.function_code, self.address, self.count
        )
        if isinstance(values, ExcCodes):
            return PDUexception(self.dev_id, self.function_code, values)
        self.is_request = False
        self.bits = cast(list[bool], values)
        return self


DecodePDU.add_pdu(PDUreadCoils)
DecodePDU.add_pdu(PDUreadDiscreteInputs)
DecodePDU.add_pdu(PDUwriteSingleCoil)
DecodePDU.add_pdu(PDUwriteMultipleCoils)
