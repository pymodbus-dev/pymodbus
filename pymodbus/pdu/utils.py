"""Contains base classes for modbus request/response/error packets."""
from __future__ import annotations

import struct


def pack_bitstring(bits: list[bool], align_byte=True) -> bytes:
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
    t_bits = bits
    bits_extra = 8 if align_byte else 16
    if (extra := len(bits) % bits_extra):
        t_bits += [False] * (bits_extra - extra)
    for byte_inx in range(0, len(t_bits), 8):
        for bit in reversed(t_bits[byte_inx:byte_inx+8]):
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
