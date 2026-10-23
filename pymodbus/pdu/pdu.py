"""Contains base classes for modbus request/response/error packets."""

from __future__ import annotations

import asyncio
import copy
import struct
from abc import abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeAlias, cast

from ..constants import ExcCodes
from ..datastore import ModbusServerContext
from ..exceptions import (
    MessageRegisterException,
    ModbusIOException,
    NotImplementedException,
)
from ..logging import Log


StoreGet: TypeAlias = Callable[
    [int, int, int, int], Awaitable[list[int] | list[bool] | ExcCodes]
]
StoreSet: TypeAlias = Callable[
    [int, int, int, Sequence[int] | Sequence[bool]], Awaitable[ExcCodes | None]
]


class OLD_pdu:  # pylint: disable=invalid-name
    """Base class for all Modbus messages."""

    function_code: int = 0
    sub_function_code: int = -1

    def __init__(
        self,
        dev_id: int = 0,
        transaction_id: int = 0,
        address: int = 0,
        count: int = 0,
        bits: Sequence[bool] | None = None,
        registers: Sequence[int] | None = None,
        status: int = 1,
    ) -> None:
        """Initialize the base data for a modbus request."""
        self.dev_id: int = dev_id
        if dev_id > 255:
            raise ModbusIOException(
                f"Invalid ID {dev_id}",
                transaction_id=transaction_id,
                dev_id=dev_id,
            )
        self.transaction_id: int = transaction_id
        self.address: int = address
        self.bits: Sequence[bool] = bits or []
        self.registers: Sequence[int] = registers or []
        self.count: int = count or len(self.registers)
        self.status: int = status
        self.exception_code: int = 0
        self.fut: asyncio.Future
        self.retries: int = 0

    @classmethod
    def decode_x_sub_function_code(cls, data: bytes) -> int:
        """Decode sub function code."""
        _ = data
        return -1

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return False

    def verifyCount(self, max_count: int, count: int = -1) -> None:
        """Validate API supplied count."""
        if count == -1:
            count = self.count
        if not 1 <= count <= max_count:
            raise ValueError(f"1 <= count {count} <= {max_count} !")

    def verifyAddress(self, address: int = -1) -> None:
        """Validate API supplied address."""
        if address == -1:
            address = self.address
        if not 0 <= address <= 65535:
            raise ValueError(f"0 <= address {address} <= 65535 !")

    def __str__(self) -> str:
        """Build a representation of a Modbus response."""
        return (
            f"{self.__class__.__name__}("
            f"dev_id={self.dev_id}, "
            f"transaction_id={self.transaction_id}, "
            f"address={self.address}, "
            f"count={self.count}, "
            f"bits={self.bits!s}, "
            f"registers={self.registers!s}, "
            f"status={self.status!s}, "
            f"retries={self.retries})"
        )

    @abstractmethod
    def x_encode(self) -> bytes:
        """Encode the message."""

    @abstractmethod
    def x_decode(self, data: bytes) -> None:
        """Decode data part of the message."""

    async def datastore_update(
        self, context: ModbusServerContext, device_id: int
    ) -> OLD_pdu:
        """Update diagnostic request on the given device."""
        _ = context, device_id
        raise NotImplementedException(
            f"datastore_update() not implemented {self.__class__.__name__}"
        )

    @classmethod
    @abstractmethod
    def x_calculateRtuFrameSize(cls, data: bytes) -> int:
        """Calculate the size of a PDU."""


class ModbusPdu(OLD_pdu):
    """Base class for all Modbus messages.

    The expected format as parameter and as result are:
        <payload>
    parameter uses an extra "offset" to identify the start (avoids slicing the data)
    """

    function_code: int = 0
    sub_function_code: int = -1
    MAX_COUNT: int = 65535

    def __init__(
        self,
        dev_id: int,
        is_request: bool = True,
        transaction_id: int = 0,
        address: int | None = None,
        count: int | None = None,
    ) -> None:
        """Initialize the base data for a modbus request."""
        super().__init__(dev_id)
        if 255 < dev_id < 0:
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
        if count is not None:
            if not 0 < count <= self.MAX_COUNT:
                raise ModbusIOException(
                    "Invalid count({count})",
                    dev_id=dev_id,
                    function_code=self.function_code,
                    transaction_id=transaction_id,
                )
            self.count: int = count

    def isError(self) -> bool:
        """Check if the error is a success or failure."""
        return False

    def __str__(self) -> str:
        """Build representation of pdu."""
        return (
            f"{self.__class__.__name__}-{'request' if self.is_request else 'response'} "
            f"(dev_id={self.dev_id}, function_code={self.function_code}, transaction_id={self.transaction_id}"
            f", address={self.address}"
            if self.address
            else f", count={self.count}"
            if self.count
            else ""
        )

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

    # redirect new calls to old calls

    def x_encode(self) -> bytes:
        """Encode the message."""
        return self.to_bytes()

    def x_decode(self, data: bytes) -> None:
        """Decode data part of the message."""
        self.from_bytes(0, data)

    @classmethod
    def x_calculateRtuFrameSize(cls, data: bytes) -> int:
        """Calculate the size of a PDU."""
        _ = data
        raise NotImplementedException("x_calculateRtuFrameSize called in new PDU")

    async def datastore_update(
        self, context: ModbusServerContext, device_id: int
    ) -> OLD_pdu:
        """Calculate the size of a PDU."""
        return cast(
            OLD_pdu,
            await self.build_response(context.async_getValues, context.async_setValues),
        )


class PDUexception(ModbusPdu):
    """Base class for a modbus exception PDU."""

    def __init__(
        self,
        dev_id: int,
        x_function_code: int,
        x_exception_code: int,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(dev_id, **kwargs)
        self.function_code = x_function_code | 0x80 or 0
        self.exception_code = x_exception_code or 0

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
        """Get bits from datastore."""
        return self


class DecodePDU:
    """Decode pdu requests/responses (server/client)."""

    pdu_table: dict[int, type[ModbusPdu]] = {}
    pdu_sub_table: dict[int, dict[int, type[ModbusPdu]]] = {}
    pdu_x_table: dict[int, tuple[type[OLD_pdu], type[OLD_pdu]]] = {}
    pdu_x_sub_table: dict[int, dict[int, tuple[type[OLD_pdu], type[OLD_pdu]]]] = {}

    def __init__(self, is_server: bool) -> None:
        """Initialize function_tables."""
        self.pdu_inx = 0 if is_server else 1
        self.is_server = is_server

    def _lookupPduClass(self, data: bytes) -> type[OLD_pdu] | type[ModbusPdu] | None:
        """Use `function_code` to determine the class of the PDU."""
        if (func_code := int(data[1])) > 0x80:
            return PDUexception
        if not (pdu := self.pdu_table.get(func_code, None)):
            if not (pdu := self.pdu_x_table.get(func_code, (None, None))[self.pdu_inx]):
                return None
            if (sub_func_code := pdu.decode_x_sub_function_code(data)) < 0:
                return pdu
            return self.pdu_x_sub_table[func_code].get(sub_func_code, (None, None))[
                self.pdu_inx
            ]
        if (sub_func_code := pdu.decode_sub_function_code(0, data)) < 0:
            return pdu
        return self.pdu_sub_table[func_code].get(sub_func_code, None)

    def list_function_codes(self):
        """Return list of function codes."""
        return list(self.pdu_x_table)

    @classmethod
    def add_pdu(cls, pdu: type[ModbusPdu]):
        """Register request/response."""
        cls.pdu_table[pdu.function_code] = pdu
        if pdu.sub_function_code > 0:
            if pdu.function_code not in cls.pdu_sub_table:
                cls.pdu_sub_table[pdu.function_code] = {}
            cls.pdu_sub_table[pdu.function_code][pdu.sub_function_code] = pdu

    @classmethod
    def add_x_pdu(cls, req: type[OLD_pdu], resp: type[OLD_pdu]):
        """Register request/response."""
        cls.pdu_x_table[req.function_code] = (req, resp)

    @classmethod
    def add_x_sub_pdu(cls, req: type[OLD_pdu], resp: type[OLD_pdu]):
        """Register request/response."""
        if req.function_code not in cls.pdu_x_sub_table:
            cls.pdu_x_sub_table[req.function_code] = {}
        cls.pdu_x_sub_table[req.function_code][req.sub_function_code] = (req, resp)

    def register(self, custom_class: type[OLD_pdu]) -> None:
        """Register a function and sub function class with the decoder."""
        if not issubclass(custom_class, OLD_pdu):
            raise MessageRegisterException(
                f'"{custom_class.__class__.__name__}" is Not a valid Modbus Message'
                ". Class needs to be derived from `OLD_pdu` "
            )
        if "pdu_x_table" not in self.__dict__:
            self.pdu_x_table = copy.deepcopy(DecodePDU.pdu_x_table)
        self.pdu_x_table[custom_class.function_code] = (custom_class, custom_class)

    def decode(self, frame: bytes) -> OLD_pdu:
        """Decode a frame."""
        if not frame:
            raise ModbusIOException("Cannot decode empty frame")
        function_code = 0
        try:
            if (function_code := int(frame[0])) > 0x80:
                pdu_exp = PDUexception(0, (function_code & 0x7F), 0)
                pdu_exp.from_bytes(0, frame)
                return pdu_exp
            if not (pdu_class := self._lookupPduClass(b"\x00" + frame)):
                raise ModbusIOException(
                    f"Unknown response {function_code}", function_code=function_code
                )
            if hasattr(pdu_class, "from_bytes"):
                pdu_new = pdu_class(0, is_request=self.is_server)  # type: ignore[call-arg]
                pdu_new.from_bytes(1, frame)  # type: ignore[attr-defined]
                pdu = cast(OLD_pdu, pdu_new)
            else:
                pdu = pdu_class(0)
                pdu.x_decode(frame[1:])
            Log.debug(
                "decoded PDU function_code({} sub {}) -> {} ",
                pdu.function_code,
                pdu.sub_function_code,
                str(pdu),
            )
            return pdu
        except (ValueError, IndexError, struct.error) as exc:
            raise ModbusIOException(
                f"Unable to decode frame {exc}", function_code=function_code
            ) from exc

    def calculateRtuFrameSize(self, data: bytes) -> int:
        """Calculate the size of a PDU."""
        if not (pdu_class := self._lookupPduClass(data)):
            return 0
        if hasattr(pdu_class, "calculatePduSize"):
            return cast(ModbusPdu, pdu_class).calculatePduSize(self.is_server, 0, data)
        return pdu_class.x_calculateRtuFrameSize(data)

    def encode(self, pdu: OLD_pdu) -> bytes:
        """Calculate the size of a PDU."""
        return pdu.x_encode()
