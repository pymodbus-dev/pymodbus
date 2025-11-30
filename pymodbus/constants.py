"""Constants For Modbus Server/Client.

This is the single location for storing default
values for the servers and clients.
"""
from __future__ import annotations

import enum


INTERNAL_ERROR = "Pymodbus internal error"


class ModbusStatus(enum.IntEnum):
    """These represent various status codes in the modbus protocol.

    .. attribute:: WAITING

       This indicates that a modbus device is currently
       waiting for a given request to finish some running task.

    .. attribute:: READY

       This indicates that a modbus device is currently
       free to perform the next request task.

    .. attribute:: ON

       This indicates that the given modbus entity is on

    .. attribute:: OFF

       This indicates that the given modbus entity is off
    """

    WAITING = 0xFFFF
    READY = 0x0000
    ON = 0xFF00
    OFF = 0x0000


class ExcCodes(enum.IntEnum):
   """Represents the allowed exception codes."""

   ILLEGAL_FUNCTION = 0x01
   ILLEGAL_ADDRESS = 0x02
   ILLEGAL_VALUE = 0x03
   DEVICE_FAILURE = 0x04
   ACKNOWLEDGE = 0x05
   DEVICE_BUSY = 0x06
   NEGATIVE_ACKNOWLEDGE = 0x07
   MEMORY_PARITY_ERROR = 0x08
   GATEWAY_PATH_UNAVIABLE = 0x0A
   GATEWAY_NO_RESPONSE = 0x0B


class ModbusPlusOperation(enum.IntEnum):
    """Represents the type of modbus plus request.

    .. attribute:: GET_STATISTICS

       Operation requesting that the current modbus plus statistics
       be returned in the response.

    .. attribute:: CLEAR_STATISTICS

       Operation requesting that the current modbus plus statistics
       be cleared and not returned in the response.
    """

    GET_STATISTICS = 0x0003
    CLEAR_STATISTICS = 0x0004


class DeviceInformation(enum.IntEnum):
    """Represents what type of device information to read.

    .. attribute:: BASIC

       This is the basic (required) device information to be returned.
       This includes VendorName, ProductCode, and MajorMinorRevision
       code.

    .. attribute:: REGULAR

       In addition to basic data objects, the device provides additional
       and optional identification and description data objects. All of
       the objects of this category are defined in the standard but their
       implementation is optional.

    .. attribute:: EXTENDED

       In addition to regular data objects, the device provides additional
       and optional identification and description private data about the
       physical device itself. All of these data are device dependent.

    .. attribute:: SPECIFIC

       Request to return a single data object.
    """

    BASIC = 0x01
    REGULAR = 0x02
    EXTENDED = 0x03
    SPECIFIC = 0x04


class MoreData(enum.IntEnum):
    """Represents the more follows condition.

    .. attribute:: NOTHING

       This indicates that no more objects are going to be returned.

    .. attribute:: KEEP_READING

       This indicates that there are more objects to be returned.
    """

    NOTHING = 0x00
    KEEP_READING = 0xFF


class DataType(enum.IntEnum):
   """Register types, used to define of a group of registers.

   This is the types pymodbus recognizes, actually the modbus standard do NOT define e.g. INT32,
   but since nearly every device contain e.g. values of type INT32, it is available in pymodbus,
   with automatic conversions to/from registers.
   """

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

DATATYPE_STRUCT: dict[DataType, tuple[type | tuple[type, type], int]] = {  # pylint: disable=consider-using-namedtuple-or-dataclass
   DataType.INT16: (int, 1),
   DataType.UINT16: (int, 1),
   DataType.INT32: (int, 2),
   DataType.UINT32: (int, 2),
   DataType.INT64: (int, 4),
   DataType.UINT64: (int, 4),
   DataType.FLOAT32: (float, 2),
   DataType.FLOAT64: (float, 4),
   DataType.STRING: (str, -1),
   DataType.BITS: ((list, int), -2),
   DataType.REGISTERS: (int, 1),
}
