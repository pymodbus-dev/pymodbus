"""Simulator data model classes."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import TypeAlias, cast

from .simutils import DataType, SimUtils


SimValueType: TypeAlias = int | float | str | bytes | list[int] | list[float] | list[str] | list[bytes] | list[bool]


@dataclass
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
            address=0,
            count=1000,
            values=0x1234
            datatype=DataType.REGISTERS
        )

    Defines a range of registers (addresses) 0..999 each with the value 0x1234.


    .. code-block:: python

        SimData(
            address=0,
            count=1000,
            datatype=DataType.INVALID
        )

    Defines a range of registers (addresses) 0..999 each marked as invalid.

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
            values=0xffff,
            datatype=DataType.REGISTERS
        )
        SimData(
            address=100,
            values=[0xffff],
            datatype=DataType.REGISTERS
        )

    Each SimData defines 16 BITS (coils), with value True.

    Value are stored in registers (16bit is 1 register).

    In shared mode (coil and discrete inputs requests):
        - address refers to the register, containing individual bits,
          Individual bits within the register cannot be addressed,
          unless "use_bit_as_address" is set on the device.

    In non-shared mode (coil and discrete inputs requests)
        - address refers to the bit.
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
    #: if values= is a list, count will be applied to the whole list, e.g.
    #:
    #:    - count=3 datatype=DataType.REGISTERS values=[3,2] is 6 registers.
    #:    - count=3 datatype=DataType.INT32 values=[3,2] is 12 registers.
    #:    - count=2 datatype=DataType.STRING, values=["ABCD", 'EFGH'] is 8 registers
    count: int = 1

    #: Value/Values of datatype,
    #: will automatically be converted to registers, according to datatype.
    values: SimValueType = 0

    #: Used to check access and convert value to/from registers or mark as invalid.
    datatype: DataType = DataType.INVALID

    #: String encoding
    #:
    #: Used to convert a SimData(DataType.STRING) to registers.
    string_encoding: str = "utf-8"

    #: Mark register(s) as readonly.
    readonly: bool = False


    def __check_simple(self):
        """Check simple parameters."""
        if not isinstance(self.address, int) or not 0 <= self.address <= 65535:
            raise TypeError("0 <= address < 65535")
        if not isinstance(self.count, int) or not 1 <= self.count <= 65536:
            raise TypeError("1 <= count < 65536")
        if self.address + self.count -1 > 65535:
            raise TypeError("address= + count= outside address range")
        if not isinstance(self.datatype, DataType):
            raise TypeError("datatype= must by a DataType")
        if self.values and self.datatype == DataType.INVALID:
            raise TypeError("values= cannot be used with invalid=True")
        if isinstance(self.values, list) and not self.values:
            raise TypeError("values= list cannot be empty")
        try:
            "test string".encode(self.string_encoding)
        except (UnicodeEncodeError, LookupError) as exc:
            raise TypeError("string_encoding= not valid") from exc

    def __check_parameters(self):
        """Check all parameters."""
        self.__check_simple()
        x_values = self.values if isinstance(self.values, list) else [self.values]
        x_datatype, _x_struct, _x_len = SimUtils.DATATYPE_STRUCT[self.datatype]
        if self.datatype == DataType.BITS:
            x_datatype = bool if isinstance(x_values[0], bool) else int
        for x_value in x_values:
            if self.datatype == DataType.BITS and x_datatype is int and isinstance(x_value, bool):
                raise TypeError(f"values= {x_value} int and bool cannot be mixed")
            if not isinstance(x_value, x_datatype):
                raise TypeError(f"values= {x_value} is not {x_datatype!s}")
            if x_datatype is str and not x_value:
                raise TypeError("values= cannot contain empty string")

    def __post_init__(self):
        """Define a group of registers."""
        self.__check_parameters()

    def build_registers_bits_block(self) -> list[bool]:
        """Convert values= to registers from bits (1 bit in each register)."""
        x_values = self.values if isinstance(self.values, list) else [self.values]
        if isinstance(x_values[0], bool):
            return cast(list[bool], x_values)
        return SimUtils.registersToBits(cast(list[int], x_values))

    def build_registers_bits_shared(self) -> list[int]:
        """Convert values= to registers from bits (16 bits in each register)."""
        x_values = self.values if isinstance(self.values, list) else [self.values]
        if not isinstance(x_values[0], bool):
            return cast(list[int], x_values)
        if len(x_values) % 16:
            raise TypeError(f"SimData address={self.address} values= must be a multiple of 16")
        return SimUtils.bitsToRegisters(cast(list[bool], x_values))

    def build_registers_string(self) -> list[int]:
        """Convert values= to registers from string(s)."""
        x_values = self.values if isinstance(self.values, list) else [self.values]
        blocks_regs: list[int] = []
        for value in x_values:
            bytes_string = cast(str, value).encode(self.string_encoding)
            regs = SimUtils.bytesToRegisters(bytes_string)
            blocks_regs.extend(regs)
        return blocks_regs


    def build_registers(self, block_bits: bool) -> list[int] | list[bool]:
        """Convert values= to registers."""
        self.__check_parameters()
        if self.datatype == DataType.STRING:
            return self.build_registers_string() * self.count
        if block_bits:
            return self.build_registers_bits_block() * self.count
        if self.datatype == DataType.BITS:
            return self.build_registers_bits_shared() * self.count

        x_values = self.values if isinstance(self.values, list) else [self.values]
        _x_datatype, x_struct, _x_len = SimUtils.DATATYPE_STRUCT[self.datatype]
        blocks_regs: list[int] = []
        for v in x_values:
            byte_list = struct.pack(f">{x_struct}", v)
            blocks_regs.extend(SimUtils.bytesToRegisters(byte_list))
        return blocks_regs
