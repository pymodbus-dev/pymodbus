"""Contains base classes for modbus request/response/error packets."""

from __future__ import annotations

import struct
from abc import abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeAlias

from ..constants import ExcCodes
from ..exceptions import (
    ModbusIOException,
)
from ..logging import Log


StoreGet: TypeAlias = Callable[
    [int, int, int, int], Awaitable[list[int] | list[bool] | ExcCodes]
]
StoreSet: TypeAlias = Callable[
    [int, int, int, Sequence[int] | Sequence[bool]], Awaitable[ExcCodes | None]
]


class ModbusPdu:
    """Base class for all Modbus messages.

    The expected format as parameter and as result are:
        <payload>
    parameter uses an extra "offset" to identify the start (avoids slicing the data)
    """

    function_code: int = 0
    sub_function_code: int = -1
    MAX_COUNT: int = 2001

    def __init__(
        self,
        dev_id: int,
        is_request: bool = True,
        transaction_id: int = 0,
        address: int | None = None,
        count: int | None = None,
    ) -> None:
        """Initialize the base data for a modbus request."""
        if not 0 <= dev_id <= 255:
            raise ModbusIOException(
                "Invalid device id",
                dev_id=dev_id,
                function_code=self.function_code,
                transaction_id=transaction_id,
            )
        self.dev_id: int = dev_id
        self.is_request: bool = is_request
        self.transaction_id: int = transaction_id
        if address is not None:
            if not 0 <= address <= 65535:
                raise ModbusIOException(
                    f"Invalid address({address})",
                    dev_id=dev_id,
                    function_code=self.function_code,
                    transaction_id=transaction_id,
                )
            self.address: int = address
        else:
            self.address = 0
        if count is not None:
            if not 0 < count <= self.MAX_COUNT:
                raise ModbusIOException(
                    "Invalid count({count})",
                    dev_id=dev_id,
                    function_code=self.function_code,
                    transaction_id=transaction_id,
                )
            self.count: int = count
        else:
            self.count = 0
        self.registers: Sequence[int] = []
        self.exception_code = 0
        self.bits: Sequence[bool] = []

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return False

    def __str__(self) -> str:
        """Build representation of pdu."""
        x_type = "request" if self.is_request else "response"
        x_str = (
            f"{self.__class__.__name__}-{x_type} "
            f"(dev_id={self.dev_id}, function_code={self.function_code}, transaction_id={self.transaction_id}"
        )
        if self.address:
            x_str += f", address={self.address}"
        if self.count:
            x_str += f", count={self.count}"
        return x_str

    @classmethod
    def decode_sub_function_code(cls, offset: int, data: bytes) -> int:
        """Decode sub function code."""
        _ = offset, data
        return -1

    @classmethod
    @abstractmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""

    @abstractmethod
    def to_bytes(self) -> bytes:
        """Encode the message."""

    @abstractmethod
    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode message."""

    @abstractmethod
    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get/Set values from datastore."""


class PDUexception(ModbusPdu):
    """Base class for a modbus exception PDU."""

    def __init__(
        self,
        dev_id: int,
        function_code: int,
        exception_code: int,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(dev_id, **kwargs)
        self.function_code = function_code | 0x80 or 0
        self.exception_code = exception_code or 0

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return True

    def __str__(self) -> str:
        """Build representation of pdu."""
        return (
            super().__str__()
            + f", function_code={self.function_code}, exception_code={self.exception_code}"
        )

    @classmethod
    def calculatePduSize(cls, is_request: bool, offset: int, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 5

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return struct.pack(">B", self.exception_code)

    def from_bytes(self, offset: int, data: bytes) -> None:
        """Decode payload."""
        self.function_code = int(data[offset + 0])
        self.exception_code = int(data[offset + 1])

    async def build_response(
        self, get_values: StoreGet, set_values: StoreSet
    ) -> ModbusPdu:
        """Get from datastore."""
        return PDUexception(
            self.dev_id,
            self.function_code,
            ExcCodes.ILLEGAL_FUNCTION,
            is_request=self.is_request,
        )


class DecodePDU:
    """Decode pdu requests/responses (server/client)."""

    pdu_table: dict[int, type[ModbusPdu]] = {}
    pdu_sub_table: dict[int, dict[int, type[ModbusPdu]]] = {}

    def __init__(self, is_server: bool) -> None:
        """Initialize function_tables."""
        self.is_server = is_server

    @classmethod
    def _lookupPduClass(cls, data: bytes) -> type[ModbusPdu] | None:
        """Use `function_code` to determine the class of the PDU."""
        if (func_code := int(data[1])) > 0x80:
            return PDUexception
        if not (pdu := cls.pdu_table.get(func_code, None)):
            return None
        if (sub_func_code := pdu.decode_sub_function_code(0, data)) < 0:
            return pdu
        return cls.pdu_sub_table[func_code].get(sub_func_code, None)

    @classmethod
    def add_pdu(cls, pdu: type[ModbusPdu]):
        """Register request/response."""
        cls.pdu_table[pdu.function_code] = pdu
        if pdu.sub_function_code >= 0:
            if pdu.function_code not in cls.pdu_sub_table:
                cls.pdu_sub_table[pdu.function_code] = {}
            cls.pdu_sub_table[pdu.function_code][pdu.sub_function_code] = pdu

    def decode(self, frame: bytes) -> ModbusPdu:
        """Decode a frame."""
        if not frame:
            raise ModbusIOException("Cannot decode empty frame")
        function_code = 0
        try:
            if not (pdu_class := self._lookupPduClass(b"\x00" + frame)):
                raise ModbusIOException(
                    f"Unknown response {function_code}", function_code=function_code
                )
            pdu = pdu_class(0, is_request=self.is_server)  # type: ignore[call-arg]
            pdu.from_bytes(1, frame)  # type: ignore[attr-defined]
            Log.debug("decoded PDU " + str(pdu))
            return pdu
        except (ValueError, IndexError, struct.error) as exc:
            raise ModbusIOException(
                f"Unable to decode frame {exc}", function_code=function_code
            ) from exc

    def calculateRtuFrameSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        if not (pdu_class := self._lookupPduClass(data)):
            return 0
        return pdu_class.calculatePduSize(self.is_server, 0, data)

    def encode(self, pdu: ModbusPdu) -> bytes:
        """Create message from PDU."""
        return pdu.to_bytes()


def pack_bitstring(bits: Sequence[bool], align_byte=True) -> bytes:
    """Create a bytestring out of a list of bits.

    example::

        bits   = [True, False, False, False] +
                 [False, False, False, True] +
                 [True, False, True, False] +
                 [False, False, False, False]
        result = pack_bitstring(bits)
        bytes 0x05 0x81
    """
    ret = b""
    i = packed = 0
    t_bits = list(bits)
    bits_extra = 8 if align_byte else 16
    if extra := len(bits) % bits_extra:
        t_bits += [False] * (bits_extra - extra)
    for byte_inx in range(0, len(t_bits), 8):
        for bit in reversed(t_bits[byte_inx : byte_inx + 8]):
            packed <<= 1
            if bit:
                packed += 1
            i += 1
            if i == 8:
                ret += struct.pack(">B", packed)
                i = packed = 0
    return ret


def unpack_bitstring(data: bytes) -> list[bool]:
    """Create bit list out of a bytestring.

    example::

        bytes 0x05 0x81
        result = unpack_bitstring(bytes)

        [True, False, True, False] + [False, False, False, False]
        [True, False, False, False] + [False, False, False, True]
    """
    res = []
    for _, t_byte in enumerate(data):
        for bit in (1, 2, 4, 8, 16, 32, 64, 128):
            res.append(bool(t_byte & bit))
    return res
