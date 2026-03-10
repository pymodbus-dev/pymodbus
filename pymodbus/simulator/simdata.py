"""Simulator data model classes."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import TypeAlias, cast

from ..pdu.utils import pack_bitstring, unpack_bitstring
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
            datatype=DataType.BITS
        )
        SimData(
            address=100,
            values=[0xffff],
            datatype=DataType.BITS
        )

    Each SimData defines 16 BITS (coils), with value True.

    Value are stored in registers (16bit is 1 register), the address refers to the register, unless
    in non-shared mode where the address refers to the coil.
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

    def __check_parameters(self):
        """Check all parameters."""
        self.__check_simple()
        x_values = self.values if isinstance(self.values, list) else [self.values]
        x_datatype, _x_struct, _x_len = SimUtils.DATATYPE_STRUCT[self.datatype]
        if self.datatype == DataType.BITS:
            x_datatype = int if isinstance(x_values[0], int) else bool
        for x_value in x_values:
            if not isinstance(x_value, x_datatype):
                raise TypeError(f"values= {x_value} is not {x_datatype!s}")
            if x_datatype is str and not x_value:
                raise TypeError("values= cannot contain empty string")

    def __post_init__(self):
        """Define a group of registers."""
        self.__check_parameters()

    def build_registers_bits_block(self) -> list[int]:
        """Convert values= to registers from bits (1 bit in each register)."""
        x_values = self.values if isinstance(self.values, list) else [self.values]
        regs: list[int] = []
        if isinstance(x_values[0], bool):
            for v in x_values:
                regs.append(1 if v else 0)
        else:
            for v in cast(list[int], x_values):
                bool_list = unpack_bitstring(v.to_bytes(2, byteorder="big"))
                for i in bool_list:
                    regs.append(1 if i else 0)
        return regs

    def build_registers_bits_shared(self, endian: tuple[bool, bool]) -> list[int]:
        """Convert values= to registers from bits (16 bits in each register)."""
        x_values = self.values if isinstance(self.values, list) else [self.values]
        if isinstance(x_values[0], bool):
            if len(x_values) % 16:
                raise TypeError(f"SimData address={self.address} values= must be a multiple of 16")
            bytes_bits = bytearray(pack_bitstring(cast(list[bool], x_values)))
        else:
            bytes_bits = bytearray()
            for v in x_values:
                bytes_bits.extend(struct.pack(">H", v))
        return SimUtils.convert_bytes_registers(bytes_bits, endian[0], endian[1], 1)

    def build_registers_string(self, endian: tuple[bool, bool], string_encoding: str) -> list[int]:
        """Convert values= to registers from string(s)."""
        x_values = self.values if isinstance(self.values, list) else [self.values]
        blocks_regs: list[int] = []
        for value in x_values:
            bytes_string = cast(str, value).encode(string_encoding)
            if len(bytes_string) % 2:
                bytes_string += b"\x00"
            blocks_regs.extend(SimUtils.convert_bytes_registers(bytearray(bytes_string), endian[0], endian[1], 1))
        return blocks_regs


    def build_registers(self, endian: tuple[bool, bool], string_encoding: str, block_bits: bool) -> list[int]:
        """Convert values= to registers."""
        self.__check_parameters()
        if self.datatype == DataType.STRING:
            block_regs = self.build_registers_string(endian, string_encoding)
            return block_regs * self.count
        if self.datatype == DataType.BITS:
            if block_bits:
                return self.build_registers_bits_block()
            return self.build_registers_bits_shared(endian)

        x_values = self.values if isinstance(self.values, list) else [self.values]
        _x_datatype, x_struct, x_len = SimUtils.DATATYPE_STRUCT[self.datatype]
        blocks_regs: list[int] = []
        for v in x_values:
            byte_list = struct.pack(f">{x_struct}", v)
            blocks_regs.extend(SimUtils.convert_bytes_registers(bytearray(byte_list), endian[0], endian[1], x_len))
        return blocks_regs
