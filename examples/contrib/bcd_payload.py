"""
Modbus BCD Payload Builder
-----------------------------------------------------------

This is an example of building a custom payload builder
that can be used in the pymodbus library. Below is a 
simple binary coded decimal builder and decoder.
"""
from struct import pack, unpack
from pymodbus.constants import Endian
from pymodbus.interfaces import IPayloadBuilder
from pymodbus.utilities import pack_bitstring
from pymodbus.utilities import unpack_bitstring
from pymodbus.exceptions import ParameterException
from pymodbus.payload import BinaryPayloadDecoder


def convert_to_bcd(decimal):
    """ Converts a decimal value to a bcd value

    :param value: The decimal value to to pack into bcd
    :returns: The number in bcd form
    """
    place, bcd = 0, 0
    while decimal > 0:
        nibble = decimal % 10
        bcd += nibble << place
        decimal /= 10
        place += 4
    return bcd


def convert_from_bcd(bcd):
    """ Converts a bcd value to a decimal value

    :param value: The value to unpack from bcd
    :returns: The number in decimal form
    """
    place, decimal = 1, 0
    while bcd > 0:
        nibble = bcd & 0xf
        decimal += nibble * place
        bcd >>= 4
        place *= 10
    return decimal


def count_bcd_digits(bcd):
    """ Count the number of digits in a bcd value

    :param bcd: The bcd number to count the digits of
    :returns: The number of digits in the bcd string
    """
    count = 0
    while bcd > 0:
        count += 1
        bcd >>= 4
    return count


class BcdPayloadBuilder(IPayloadBuilder):
    """
    A utility that helps build binary coded decimal payload
    messages to be written with the various modbus messages.
    example::

        builder = BcdPayloadBuilder()
        builder.add_number(1)
        builder.add_number(int(2.234 * 1000))
        payload = builder.build()
    """

    def __init__(self, payload=None, endian=Endian.Little):
        """ Initialize a new instance of the payload builder

        :param payload: Raw payload data to initialize with
        :param endian: The endianess of the payload
        """
        self._payload = payload or []
        self._endian  = endian

    def __str__(self):
        """ Return the payload buffer as a string

        :returns: The payload buffer as a string
        """
        return ''.join(self._payload)

    def reset(self):
        """ Reset the payload buffer
        """
        self._payload = []

    def build(self):
        """ Return the payload buffer as a list

        This list is two bytes per element and can
        thus be treated as a list of registers.

        :returns: The payload buffer as a list
        """
        string = str(self)
        length = len(string)
        string = string + ('\x00' * (length % 2))
        return [string[i:i+2] for i in range(0, length, 2)]

    def add_bits(self, values):
        """ Adds a collection of bits to be encoded

        If these are less than a multiple of eight,
        they will be left padded with 0 bits to make
        it so.

        :param value: The value to add to the buffer
        """
        value = pack_bitstring(values)
        self._payload.append(value)

    def add_number(self, value, size=None):
        """ Adds any 8bit numeric type to the buffer

        :param value: The value to add to the buffer
        """
        encoded = []
        value = convert_to_bcd(value)
        size = size or count_bcd_digits(value)
        while size > 0:
            nibble = value & 0xf
            encoded.append(pack('B', nibble))
            value >>= 4
            size -= 1
        self._payload.extend(encoded)

    def add_string(self, value):
        """ Adds a string to the buffer

        :param value: The value to add to the buffer
        """
        self._payload.append(value)


class BcdPayloadDecoder(object):
    """
    A utility that helps decode binary coded decimal payload
    messages from a modbus reponse message. What follows is
    a simple example::

        decoder = BcdPayloadDecoder(payload)
        first   = decoder.decode_int(2)
        second  = decoder.decode_int(5) / 100
    """

    def __init__(self, payload):
        """ Initialize a new payload decoder

        :param payload: The payload to decode with
        """
        self._payload = payload
        self._pointer = 0x00

    @staticmethod
    def fromRegisters(registers, endian=Endian.Little):
        """ Initialize a payload decoder with the result of
        reading a collection of registers from a modbus device.

        The registers are treated as a list of 2 byte values.
        We have to do this because of how the data has already
        been decoded by the rest of the library.

        :param registers: The register results to initialize with
        :param endian: The endianess of the payload
        :returns: An initialized PayloadDecoder
        """
        if isinstance(registers, list): # repack into flat binary
            payload = ''.join(pack('>H', x) for x in registers)
            return BinaryPayloadDecoder(payload, endian)
        raise ParameterException('Invalid collection of registers supplied')

    @staticmethod
    def fromCoils(coils, endian=Endian.Little):
        """ Initialize a payload decoder with the result of
        reading a collection of coils from a modbus device.

        The coils are treated as a list of bit(boolean) values.

        :param coils: The coil results to initialize with
        :param endian: The endianess of the payload
        :returns: An initialized PayloadDecoder
        """
        if isinstance(coils, list):
            payload = pack_bitstring(coils)
            return BinaryPayloadDecoder(payload, endian)
        raise ParameterException('Invalid collection of coils supplied')

    def reset(self):
        """ Reset the decoder pointer back to the start
        """
        self._pointer = 0x00

    def decode_int(self, size=1):
        """ Decodes a int or long from the buffer
        """
        self._pointer += size
        handle = self._payload[self._pointer - size:self._pointer]
        return convert_from_bcd(handle)

    def decode_bits(self):
        """ Decodes a byte worth of bits from the buffer
        """
        self._pointer += 1
        handle = self._payload[self._pointer - 1:self._pointer]
        return unpack_bitstring(handle)

    def decode_string(self, size=1):
        """ Decodes a string from the buffer

        :param size: The size of the string to decode
        """
        self._pointer += size
        return self._payload[self._pointer - size:self._pointer]


# --------------------------------------------------------------------------- #
# Exported Identifiers
# --------------------------------------------------------------------------- #

__all__ = ["BcdPayloadBuilder", "BcdPayloadDecoder"]
