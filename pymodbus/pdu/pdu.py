"""Contains base classes for modbus request/response/error packets."""

from __future__ import annotations

import struct
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeAlias

from ..constants import MAX_TRANSACTION_ID, ExcCodes
from ..exceptions import ModbusIOException
from ..logging import Log


StoreGet: TypeAlias = Callable[
    [int, int, int, int], Awaitable[list[int] | list[bool] | ExcCodes]
]
StoreSet: TypeAlias = Callable[
    [int, int, int, Sequence[int] | Sequence[bool]], Awaitable[ExcCodes | None]
]


class ModbusPdu:
    """Base class for all Modbus messages."""

    function_code: int = -1
    sub_function_code: int = -1
    MAX_COUNT: int = 10000

    def __init__(
        self,
        is_request: bool,
        dev_id: int,
        transaction_id: int = 0,
    ) -> None:
        """Initialize the base data for a modbus request."""
        self.is_request: bool = is_request
        self.dev_id: int = dev_id
        self.transaction_id: int = transaction_id
        self.registers: Sequence[int]
        self.bits: Sequence[bool]
        self.address: int
        self.count: int
        if not 0 <= self.dev_id <= 255:
            self.raiseExp("Invalid device id({dev_id})")
        if not 0 <= self.transaction_id <= MAX_TRANSACTION_ID:
            self.raiseExp("Invalid device id({dev_id})")

    def raiseExp(self, error: str) -> None:
        """Raise exception, with known data."""
        raise ModbusIOException(
            error,
            dev_id=self.dev_id,
            function_code=self.function_code,
            transaction_id=self.transaction_id,
        )

    def respondExp(self, exc_code: ExcCodes) -> PDUexception:
        """Build exception response."""
        return PDUexception(
            self.dev_id,
            self.function_code,
            exc_code,
            transaction_id=self.transaction_id,
        )

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return False

    def __str__(self) -> str:
        """Build representation of pdu."""
        x_type = "request" if self.is_request else "response"
        return (
            f"{self.__class__.__name__}-{x_type} "
            f"(dev_id={self.dev_id}, function_code={self.function_code}, transaction_id={self.transaction_id}"
        )

    @classmethod
    def decode_sub_function_code(cls, data: bytes) -> int:
        """Decode sub function code."""
        _ = data
        return -1

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        _ = data
        return 2

    def preamble(self) -> bytes:
        """Encode the message."""
        return struct.pack(">BB", self.dev_id, self.function_code)

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return b""

    def from_bytes(self, data: bytes) -> str | None:
        """Decode message."""
        self.dev_id, self.function_code = struct.unpack(">BB", data[:2])

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get/Set values from datastore."""
        _ = v_get, v_set
        return self.respondExp(ExcCodes.DEVICE_BUSY)


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
        super().__init__(False, dev_id, **kwargs)
        self.function_code = function_code | 0x80
        self.exception_code = exception_code

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return True

    def __str__(self) -> str:
        """Build representation of pdu."""
        return super().__str__() + f", exception_code={self.exception_code}"

    def calculatePduSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        return 3

    def to_bytes(self) -> bytes:
        """Encode the message."""
        return self.preamble() + struct.pack(">B", self.exception_code)

    def from_bytes(self, data: bytes) -> str | None:
        """Decode payload."""
        self.function_code, self.exception_code = struct.unpack(">BB", data[1:])

    async def build_response(self, v_get: StoreGet, v_set: StoreSet) -> ModbusPdu:
        """Get from datastore."""
        self.exception_code = ExcCodes.ILLEGAL_FUNCTION
        return self


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
        if len(data) < 3:
            return None
        if (func_code := int(data[1])) > 0x80:
            return PDUexception
        if not (pdu := cls.pdu_table.get(func_code, None)):
            return None
        if (sub_func_code := pdu.decode_sub_function_code(data)) < 0:
            return pdu
        return cls.pdu_sub_table[func_code].get(sub_func_code, None)

    @classmethod
    def add_pdu(cls, pdu: type[ModbusPdu]) -> None:
        """Register request/response."""
        cls.pdu_table[pdu.function_code] = pdu
        if pdu.sub_function_code >= 0:
            if pdu.function_code not in cls.pdu_sub_table:
                cls.pdu_sub_table[pdu.function_code] = {}
            cls.pdu_sub_table[pdu.function_code][pdu.sub_function_code] = pdu

    def decode(self, data: bytes) -> ModbusPdu:
        """Decode a frame."""
        if not data:
            raise ModbusIOException("Cannot decode empty frame")
        function_code = 0
        if not (pdu_class := self._lookupPduClass(data)):
            raise ModbusIOException(
                f"Unknown response {function_code}", function_code=function_code
            )
        pdu = pdu_class(self.is_server, 0)
        if len(data) != pdu.calculatePduSize(data):
            raise ModbusIOException(
                f"Unknown response {function_code}", function_code=function_code
            )
        pdu.from_bytes(data)
        Log.debug("decoded PDU " + str(pdu))
        return pdu

    def calculateRtuFrameSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        if not (pdu_class := self._lookupPduClass(data)):
            return 0
        pdu = pdu_class(self.is_server, 0)
        calc_len = pdu.calculatePduSize(data)
        if (x := len(data)) != (calc_len := pdu.calculatePduSize(data)):
            raise ModbusIOException(
                f"Wrong data length for {pdu.function_code} got {x} expected {calc_len} ",
                function_code=pdu.function_code,
            )
        return calc_len + 2

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
