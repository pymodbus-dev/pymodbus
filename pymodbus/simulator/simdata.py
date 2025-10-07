"""Simulator data model classes.

**REMARK** This code is experimental and not integrated into production.
"""
from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeAlias, cast

from ..constants import DATATYPE_STRUCT, DataType
from ..pdu import ExceptionResponse


SimValueTypeSimple: TypeAlias = int | float | str | bytes
SimValueType: TypeAlias = SimValueTypeSimple | list[SimValueTypeSimple | bool]
SimAction: TypeAlias = Callable[[int, int, list[int]], Awaitable[list[int] | ExceptionResponse]]

@dataclass(order=True, frozen=True)
class SimData:
    """Configure a group of continuous identical values/registers.

    **Examples**:

    .. code-block:: python

        SimData(
            address=100,
            count=5,
            values=12345678
            datatype=DataType.INT32
        )
        SimData(
            address=100,
            values=[1, 2, 3, 4, 5]
            datatype=DataType.INT32
        )

    Each SimData defines 5 INT32 in total 10 registers (address 100-109)

    .. code-block:: python

        SimData(
            address=100,
            count=16,
            values=True
            datatype=DataType.BITS
        )
        SimData(
            address=100,
            values=[True] * 16
            datatype=DataType.BITS
        )
        SimData(
            address=100,
            values=0xffff
            datatype=DataType.BITS
        )
        SimData(
            address=100,
            values=[0xffff]
            datatype=DataType.BITS
        )

    Each SimData defines 16 BITS (coils), with value True.

    Value are stored in registers (16bit is 1 register), the address refer to the register.

    **Remark** when using offsets, only bit 0 of each register is used!

    .. code-block:: python

        SimData(
            address=0,
            count=1000,
            values=0x1234
            datatype=DataType.REGISTERS
        )

    Defines a range of addresses 0..999 each with the value 0x1234.
    """

    #: Address of first register, starting with 0 (identical to the requests)
    address: int

    #: Count of datatype e.g.
    #:
    #:    - count=3 datatype=DataType.REGISTERS is 3 registers.
    #:    - count=3 datatype=DataType.INT32 is 6 registers.
    #:    - count=1 datatype=DataType.STRING, values="ABCD" is 2 registers
    #:    - count=2 datatype=DataType.STRING, values="ABCD" is 4 registers
    #:
    #: Count cannot be used if values= is a list
    count: int = 1

    #: Value/Values of datatype,
    #: will automatically be converted to registers, according to datatype.
    values: SimValueType = 0

    #: Used to check access and convert value to/from registers.
    datatype: DataType = DataType.REGISTERS

    #: Optional function to call when registers are being read/written.
    #:
    #: **Example function:**
    #:
    #: .. code-block:: python
    #:
    #:     async def my_action(
    #:         function_code: int,
    #:         address: int,
    #:         registers: list[int]) -> list[int] | ExceptionResponse:
    #:
    #          return registers
    #:
    #: .. tip:: use functools.partial to add extra parameters if needed.
    action: SimAction | None = None

    #: Mark register(s) as readonly.
    readonly: bool = False

    #: Mark register(s) as invalid.
    #: **remark** only to be used with address= and count=
    invalid: bool = False

    def __check_simple(self):
        """Check simple parameters."""
        if not isinstance(self.address, int) or not 0 <= self.address <= 65535:
            raise TypeError("0 <= address < 65535")
        if not isinstance(self.count, int) or not 1 <= self.count <= 65536:
            raise TypeError("1 <= count < 65536")
        if not 1 <= self.address + self.count <= 65536:
            raise TypeError("1 <= address + count < 65536")
        if not isinstance(self.datatype, DataType):
            raise TypeError("datatype= must by an DataType")
        if self.action and not (callable(self.action) and inspect.iscoroutinefunction(self.action)):
            raise TypeError("action= not a async function")

    def __post_init__(self):
        """Define a group of registers."""
        self.__check_simple()
        if self.datatype == DataType.STRING:
            if not isinstance(self.values, str):
                raise TypeError("datatype=DataType.STRING only allows values=\"string\"")
            x_datatype, x_len = str, int((len(self.values) +1) / 2)
        else:
            x_datatype, x_len = DATATYPE_STRUCT[self.datatype]
            if not isinstance(self.values, list):
                super().__setattr__("values", [self.values])
            for x_value in cast(list, self.values):
                if not isinstance(x_value, x_datatype):
                    raise TypeError(f"value= can only contain {x_datatype!s}")
        super().__setattr__("register_count", self.count * x_len)
        super().__setattr__("type_size", x_len)
