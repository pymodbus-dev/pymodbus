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

class SimUtils:
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


    def __init__(self):
        """Ensure that class is not instantiated."""
        raise RuntimeError("SimUtils may not be instantiated.")

    @classmethod
    def registersToBits(cls, registers: list[int]) -> list[bool]:
        """Convert list of registers to list of bool (bit 0 first)."""
        bits: list[bool] = []
        for entry in registers:
            bit_str = format(entry, '016b')
            new_bits = []
            for i in bit_str:
                new_bits.append(i == "1")
            new_bits.reverse()
            bits.extend(new_bits)
        return bits

    @classmethod
    def bitsToRegisters(cls, bits: list[bool]) -> list[int]:
        """Convert list  of bits to registers (bit 0 first, divided in 16bits)."""
        bit_len = len(bits)
        if bit_len % 16:
            raise TypeError("bits must be a multiple of 16")
        registers = []
        for i in range(int(bit_len / 16)):
            offset = i*16
            reg = 0
            for i, x in enumerate(bits[offset:offset+16]):
                if x:
                    reg += 1 << i
            registers.append(reg)
        return registers

    @classmethod
    def mergeBitsToRegisters(cls, bit_offset: int, registers: list[int], bits: list[bool]) -> None:
        """Merge list of bits into registers in place."""
        new_bits = cls.registersToBits(registers)
        new_bits[bit_offset:bit_offset+len(bits)] = bits
        registers[0:] = cls.bitsToRegisters(new_bits)

    @classmethod
    def bytesToRegisters(cls, byte_list: bytes) -> list[int]:
        """Convert bytes into registers."""
        if len(byte_list) % 2:
            byte_list += b"\x00"
        return[
            int.from_bytes(byte_list[x : x + 2], "big")
            for x in range(0, len(byte_list), 2)
        ]
