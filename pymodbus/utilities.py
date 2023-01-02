"""Modbus Utilities.

A collection of utilities for packing data, unpacking
data computing checksums, and decode checksums.
"""
# pylint: disable=missing-type-doc
import struct


class ModbusTransactionState:  # pylint: disable=too-few-public-methods
    """Modbus Client States."""

    IDLE = 0
    SENDING = 1
    WAITING_FOR_REPLY = 2
    WAITING_TURNAROUND_DELAY = 3
    PROCESSING_REPLY = 4
    PROCESSING_ERROR = 5
    TRANSACTION_COMPLETE = 6
    RETRYING = 7
    NO_RESPONSE_STATE = 8

    @classmethod
    def to_string(cls, state):
        """Convert to string."""
        states = {
            ModbusTransactionState.IDLE: "IDLE",
            ModbusTransactionState.SENDING: "SENDING",
            ModbusTransactionState.WAITING_FOR_REPLY: "WAITING_FOR_REPLY",
            ModbusTransactionState.WAITING_TURNAROUND_DELAY: "WAITING_TURNAROUND_DELAY",
            ModbusTransactionState.PROCESSING_REPLY: "PROCESSING_REPLY",
            ModbusTransactionState.PROCESSING_ERROR: "PROCESSING_ERROR",
            ModbusTransactionState.TRANSACTION_COMPLETE: "TRANSACTION_COMPLETE",
            ModbusTransactionState.RETRYING: "RETRYING TRANSACTION",
        }
        return states.get(state, None)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def default(value):
    """Return the default value of object.

    :param value: The value to get the default of
    :returns: The default value
    """
    return type(value)()


def dict_property(store, index):
    """Create class properties from a dictionary.

    Basically this allows you to remove a lot of possible
    boilerplate code.

    :param store: The store store to pull from
    :param index: The index into the store to close over
    :returns: An initialized property set
    """
    if hasattr(store, "__call__"):
        getter = lambda self: store(  # pylint: disable=unnecessary-lambda-assignment
            self
        )[index]
        setter = lambda self, value: store(  # pylint: disable=unnecessary-dunder-call,unnecessary-lambda-assignment
            self
        ).__setitem__(
            index, value
        )
    elif isinstance(store, str):
        getter = lambda self: self.__getattribute__(  # pylint: disable=unnecessary-dunder-call,unnecessary-lambda-assignment
            store
        )[
            index
        ]
        setter = lambda self, value: self.__getattribute__(  # pylint: disable=unnecessary-dunder-call,unnecessary-lambda-assignment
            store
        ).__setitem__(
            index, value
        )
    else:
        getter = lambda self: store[  # pylint: disable=unnecessary-lambda-assignment
            index
        ]
        setter = lambda self, value: store.__setitem__(  # pylint: disable=unnecessary-dunder-call,unnecessary-lambda-assignment
            index, value
        )

    return property(getter, setter)


# --------------------------------------------------------------------------- #
# Bit packing functions
# --------------------------------------------------------------------------- #
def pack_bitstring(bits):
    """Create a string out of an array of bits.

    :param bits: A bit array

    example::

        bits   = [False, True, False, True]
        result = pack_bitstring(bits)
    """
    ret = b""
    i = packed = 0
    for bit in bits:
        if bit:
            packed += 128
        i += 1
        if i == 8:
            ret += struct.pack(">B", packed)
            i = packed = 0
        else:
            packed >>= 1
    if 0 < i < 8:
        packed >>= 7 - i
        ret += struct.pack(">B", packed)
    return ret


def unpack_bitstring(string):
    """Create bit array out of a string.

    :param string: The modbus data packet to decode

    example::

        bytes  = "bytes to decode"
        result = unpack_bitstring(bytes)
    """
    byte_count = len(string)
    bits = []
    for byte in range(byte_count):
        value = int(int(string[byte]))
        for _ in range(8):
            bits.append((value & 1) == 1)
            value >>= 1
    return bits


def make_byte_string(byte_string):
    """Return byte string from a given string, python3 specific fix.

    :param byte_string:
    :return:
    """
    if isinstance(byte_string, str):
        byte_string = byte_string.encode()
    return byte_string


# --------------------------------------------------------------------------- #
# Error Detection Functions
# --------------------------------------------------------------------------- #


def __generate_crc16_table():
    """Generate a crc16 lookup table.

    .. note:: This will only be generated once
    """
    result = []
    for byte in range(256):
        crc = 0x0000
        for _ in range(8):
            if (byte ^ crc) & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
            byte >>= 1
        result.append(crc)
    return result


__crc16_table = __generate_crc16_table()


def computeCRC(data):  # pylint: disable=invalid-name
    """Compute a crc16 on the passed in string.

    For modbus, this is only used on the binary serial protocols (in this
    case RTU).

    The difference between modbus's crc16 and a normal crc16
    is that modbus starts the crc value out at 0xffff.

    :param data: The data to create a crc16 of
    :returns: The calculated CRC
    """
    crc = 0xFFFF
    for data_byte in data:
        idx = __crc16_table[(crc ^ int(data_byte)) & 0xFF]
        crc = ((crc >> 8) & 0xFF) ^ idx
    swapped = ((crc << 8) & 0xFF00) | ((crc >> 8) & 0x00FF)
    return swapped


def checkCRC(data, check):  # pylint: disable=invalid-name
    """Check if the data matches the passed in CRC.

    :param data: The data to create a crc16 of
    :param check: The CRC to validate
    :returns: True if matched, False otherwise
    """
    return computeCRC(data) == check


def computeLRC(data):  # pylint: disable=invalid-name
    """Use to compute the longitudinal redundancy check against a string.

    This is only used on the serial ASCII
    modbus protocol. A full description of this implementation
    can be found in appendix B of the serial line modbus description.

    :param data: The data to apply a lrc to
    :returns: The calculated LRC

    """
    lrc = sum(int(a) for a in data) & 0xFF
    lrc = (lrc ^ 0xFF) + 1
    return lrc & 0xFF


def checkLRC(data, check):  # pylint: disable=invalid-name
    """Check if the passed in data matches the LRC.

    :param data: The data to calculate
    :param check: The LRC to validate
    :returns: True if matched, False otherwise
    """
    return computeLRC(data) == check


def rtuFrameSize(data, byte_count_pos):  # pylint: disable=invalid-name
    """Calculate the size of the frame based on the byte count.

    :param data: The buffer containing the frame.
    :param byte_count_pos: The index of the byte count in the buffer.
    :returns: The size of the frame.

    The structure of frames with a byte count field is always the
    same:

    - first, there are some header fields
    - then the byte count field
    - then as many data bytes as indicated by the byte count,
    - finally the CRC (two bytes).

    To calculate the frame size, it is therefore sufficient to extract
    the contents of the byte count field, add the position of this
    field, and finally increment the sum by three (one byte for the
    byte count field, two for the CRC).
    """
    return int(data[byte_count_pos]) + byte_count_pos + 3


def hexlify_packets(packet):
    """Return hex representation of bytestring received.

    :param packet:
    :return:
    """
    if not packet:
        return ""
    return " ".join([hex(int(x)) for x in packet])


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    "pack_bitstring",
    "unpack_bitstring",
    "default",
    "computeCRC",
    "checkCRC",
    "computeLRC",
    "checkLRC",
    "rtuFrameSize",
]
