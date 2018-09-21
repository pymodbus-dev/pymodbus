"""
Modbus Utilities
-----------------

A collection of utilities for packing data, unpacking
data computing checksums, and decode checksums.
"""
from pymodbus.compat import int2byte, byte2int, IS_PYTHON3
from six import string_types


class ModbusTransactionState(object):
    """
    Modbus Client States
    """
    IDLE = 0
    SENDING = 1
    WAITING_FOR_REPLY = 2
    WAITING_TURNAROUND_DELAY = 3
    PROCESSING_REPLY = 4
    PROCESSING_ERROR = 5
    TRANSACTION_COMPLETE = 6

    @classmethod
    def to_string(cls, state):
        states = {
            ModbusTransactionState.IDLE: "IDLE",
            ModbusTransactionState.SENDING: "SENDING",
            ModbusTransactionState.WAITING_FOR_REPLY: "WAITING_FOR_REPLY",
            ModbusTransactionState.WAITING_TURNAROUND_DELAY: "WAITING_TURNAROUND_DELAY",
            ModbusTransactionState.PROCESSING_REPLY: "PROCESSING_REPLY",
            ModbusTransactionState.PROCESSING_ERROR: "PROCESSING_ERROR",
            ModbusTransactionState.TRANSACTION_COMPLETE: "TRANSACTION_COMPLETE"
        }
        return states.get(state, None)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def default(value):
    """
    Given a python object, return the default value
    of that object.

    :param value: The value to get the default of
    :returns: The default value
    """
    return type(value)()


def dict_property(store, index):
    """ Helper to create class properties from a dictionary.
    Basically this allows you to remove a lot of possible
    boilerplate code.

    :param store: The store store to pull from
    :param index: The index into the store to close over
    :returns: An initialized property set
    """
    if hasattr(store, '__call__'):
        getter = lambda self: store(self)[index]
        setter = lambda self, value: store(self).__setitem__(index, value)
    elif isinstance(store, str):
        getter = lambda self: self.__getattribute__(store)[index]
        setter = lambda self, value: self.__getattribute__(store).__setitem__(
            index, value)
    else:
        getter = lambda self: store[index]
        setter = lambda self, value: store.__setitem__(index, value)

    return property(getter, setter)


# --------------------------------------------------------------------------- #
# Bit packing functions
# --------------------------------------------------------------------------- #
def pack_bitstring(bits):
    """ Creates a string out of an array of bits

    :param bits: A bit array

    example::

        bits   = [False, True, False, True]
        result = pack_bitstring(bits)
    """
    ret = b''
    i = packed = 0
    for bit in bits:
        if bit:
            packed += 128
        i += 1
        if i == 8:
            ret += int2byte(packed)
            i = packed = 0
        else:
            packed >>= 1
    if 0 < i < 8:
        packed >>= (7 - i)
        ret += int2byte(packed)
    return ret


def unpack_bitstring(string):
    """ Creates bit array out of a string

    :param string: The modbus data packet to decode

    example::

        bytes  = 'bytes to decode'
        result = unpack_bitstring(bytes)
    """
    byte_count = len(string)
    bits = []
    for byte in range(byte_count):
        if IS_PYTHON3:
            value = byte2int(int(string[byte]))
        else:
            value = byte2int(string[byte])
        for _ in range(8):
            bits.append((value & 1) == 1)
            value >>= 1
    return bits


def make_byte_string(s):
    """
    Returns byte string from a given string, python3 specific fix
    :param s:
    :return:
    """
    if IS_PYTHON3 and isinstance(s, string_types):
        s = s.encode()
    return s
# --------------------------------------------------------------------------- #
# Error Detection Functions
# --------------------------------------------------------------------------- #
def __generate_crc16_table():
    """ Generates a crc16 lookup table

    .. note:: This will only be generated once
    """
    result = []
    for byte in range(256):
        crc = 0x0000
        for _ in range(8):
            if (byte ^ crc) & 0x0001:
                crc = (crc >> 1) ^ 0xa001
            else: crc >>= 1
            byte >>= 1
        result.append(crc)
    return result

__crc16_table = __generate_crc16_table()


def computeCRC(data):
    """ Computes a crc16 on the passed in string. For modbus,
    this is only used on the binary serial protocols (in this
    case RTU).

    The difference between modbus's crc16 and a normal crc16
    is that modbus starts the crc value out at 0xffff.

    :param data: The data to create a crc16 of
    :returns: The calculated CRC
    """
    crc = 0xffff
    for a in data:
        idx = __crc16_table[(crc ^ byte2int(a)) & 0xff]
        crc = ((crc >> 8) & 0xff) ^ idx
    swapped = ((crc << 8) & 0xff00) | ((crc >> 8) & 0x00ff)
    return swapped


def checkCRC(data, check):
    """ Checks if the data matches the passed in CRC

    :param data: The data to create a crc16 of
    :param check: The CRC to validate
    :returns: True if matched, False otherwise
    """
    return computeCRC(data) == check


def computeLRC(data):
    """ Used to compute the longitudinal redundancy check
    against a string. This is only used on the serial ASCII
    modbus protocol. A full description of this implementation
    can be found in appendex B of the serial line modbus description.

    :param data: The data to apply a lrc to
    :returns: The calculated LRC

    """
    lrc = sum(byte2int(a) for a in data) & 0xff
    lrc = (lrc ^ 0xff) + 1
    return lrc & 0xff


def checkLRC(data, check):
    """ Checks if the passed in data matches the LRC

    :param data: The data to calculate
    :param check: The LRC to validate
    :returns: True if matched, False otherwise
    """
    return computeLRC(data) == check


def rtuFrameSize(data, byte_count_pos):
    """ Calculates the size of the frame based on the byte count.

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
    return byte2int(data[byte_count_pos]) + byte_count_pos + 3


def hexlify_packets(packet):
    """
    Returns hex representation of bytestring recieved
    :param packet:
    :return:
    """
    if not packet:
        return ''
    return " ".join([hex(byte2int(x)) for x in packet])
# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    'pack_bitstring', 'unpack_bitstring', 'default',
    'computeCRC', 'checkCRC', 'computeLRC', 'checkLRC', 'rtuFrameSize'
]
