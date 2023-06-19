"""Constants For Modbus Server/Client.

This is the single location for storing default
values for the servers and clients.
"""

INTERNAL_ERROR = "Pymodbus internal error"


class ModbusStatus:  # pylint: disable=too-few-public-methods
    """These represent various status codes in the modbus protocol.

    .. attribute:: Waiting

       This indicates that a modbus device is currently
       waiting for a given request to finish some running task.

    .. attribute:: Ready

       This indicates that a modbus device is currently
       free to perform the next request task.

    .. attribute:: On

       This indicates that the given modbus entity is on

    .. attribute:: Off

       This indicates that the given modbus entity is off

    .. attribute:: SlaveOn

       This indicates that the given modbus slave is running

    .. attribute:: SlaveOff

       This indicates that the given modbus slave is not running
    """

    Waiting = 0xFFFF
    Ready = 0x0000
    On = 0xFF00
    Off = 0x0000
    SlaveOn = 0xFF
    SlaveOff = 0x00

    def __init__(self):
        """Prohibit objects."""
        raise RuntimeError(INTERNAL_ERROR)


class Endian:  # pylint: disable=too-few-public-methods
    """An enumeration representing the various byte endianness.

    .. attribute:: Auto

       This indicates that the byte order is chosen by the
       current native environment.

    .. attribute:: Big

       This indicates that the bytes are in big endian format

    .. attribute:: Little

       This indicates that the bytes are in little endian format

    .. note:: I am simply borrowing the format strings from the
       python struct module for my convenience.
    """

    Auto = "@"
    Big = ">"
    Little = "<"

    def __init__(self):
        """Prohibit objects."""
        raise RuntimeError(INTERNAL_ERROR)


class ModbusPlusOperation:  # pylint: disable=too-few-public-methods
    """Represents the type of modbus plus request.

    .. attribute:: GetStatistics

       Operation requesting that the current modbus plus statistics
       be returned in the response.

    .. attribute:: ClearStatistics

       Operation requesting that the current modbus plus statistics
       be cleared and not returned in the response.
    """

    GetStatistics = 0x0003
    ClearStatistics = 0x0004

    def __init__(self):
        """Prohibit objects."""
        raise RuntimeError(INTERNAL_ERROR)


class DeviceInformation:  # pylint: disable=too-few-public-methods
    """Represents what type of device information to read.

    .. attribute:: Basic

       This is the basic (required) device information to be returned.
       This includes VendorName, ProductCode, and MajorMinorRevision
       code.

    .. attribute:: Regular

       In addition to basic data objects, the device provides additional
       and optional identification and description data objects. All of
       the objects of this category are defined in the standard but their
       implementation is optional.

    .. attribute:: Extended

       In addition to regular data objects, the device provides additional
       and optional identification and description private data about the
       physical device itself. All of these data are device dependent.

    .. attribute:: Specific

       Request to return a single data object.
    """

    Basic = 0x01
    Regular = 0x02
    Extended = 0x03
    Specific = 0x04

    def __init__(self):
        """Prohibit objects."""
        raise RuntimeError(INTERNAL_ERROR)


class MoreData:  # pylint: disable=too-few-public-methods
    """Represents the more follows condition.

    .. attribute:: Nothing

       This indicates that no more objects are going to be returned.

    .. attribute:: KeepReading

       This indicates that there are more objects to be returned.
    """

    Nothing = 0x00
    KeepReading = 0xFF

    def __init__(self):
        """Prohibit objects."""
        raise RuntimeError(INTERNAL_ERROR)
