"""Simulator utility classes."""
from __future__ import annotations

import enum


class DataType(enum.IntEnum):
    """Register types, used to define of a group of registers.

    This is the types pymodbus recognizes, actually the modbus standard do NOT define e.g. INT32,
    but since nearly every device contain e.g. values of type INT32, it is available in pymodbus,
    with automatic conversions to/from registers.
    """

    #: 1 register
    INVALID = 1  # ensure values are 1++

    #: 1 integer == 1 register
    INT16 = enum.auto()

    #: 1 positive integer == 1 register
    UINT16 = enum.auto()

    #: 1 integer == 2 registers
    INT32 = enum.auto()

    #: 1 positive integer == 2 registers
    UINT32 = enum.auto()

    #: 1 integer == 4 registers
    INT64 = enum.auto()

    #: 1 positive integer == 4 register
    UINT64 = enum.auto()

    #: 1 float == 2 registers
    FLOAT32 = enum.auto()

    #: 1 float == 4 registers
    FLOAT64 = enum.auto()

    #: 1 string == (len(string) / 2) registers
    STRING = enum.auto()

    #: 16 bits == 1 register
    BITS = enum.auto()

    #: Registers == 2 bytes (identical to UINT16)
    REGISTERS = enum.auto()

class SimUtils:  # pylint: disable=too-few-public-methods
    """Define common set of utilitites."""

    DATATYPE_STRUCT: dict[DataType, tuple[type, str, int]] = {
        DataType.REGISTERS: (int, "h", 1),
        DataType.INT16: (int, "h", 1),
        DataType.UINT16: (int, "H", 1),
        DataType.INT32: (int, "i", 2),
        DataType.UINT32: (int, "I", 2),
        DataType.INT64: (int, "q", 4),
        DataType.UINT64: (int, "Q", 4),
        DataType.FLOAT32: (float, "f", 2),
        DataType.FLOAT64: (float, "d", 4),
        DataType.STRING: (str, "s", 0),
        DataType.BITS: (bool, "bits", 0),
        DataType.INVALID: (int, "h", 1)
    }

    RunTimeFlag_TYPE     = 2**4 -1 # Isolate number of registers
    RunTimeFlag_READONLY = 2**4    # only read is allowed

    @classmethod
    def convert_bytes_registers(cls, byte_list: bytearray, word_order: str, byte_order: bool, data_type_len: int) -> list[int]:
        """Convert bytearray to registers."""
        if byte_order:
            regs = [
                int.from_bytes(byte_list[x : x + 2], "big")
                for x in range(0, len(byte_list), 2)
            ]
        else:
            regs = [
                int.from_bytes([byte_list[x+1],  byte_list[x]], "big")
                for x in range(0, len(byte_list), 2)
            ]
        if word_order == "big":
            return regs
        reversed_regs: list[int] = []
        for x in range(0, len(regs), data_type_len):
            single_value_regs = regs[x: x + data_type_len]
            single_value_regs.reverse()
            reversed_regs = reversed_regs + single_value_regs
        return reversed_regs
