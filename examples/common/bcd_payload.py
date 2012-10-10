'''
Modbus BCD Payload Builder
-----------------------------------------------------------

This is an example of building a custom payload builder
that can be used in the pymodbus library. Below is a 
simple binary coded decimal builder and decoder.
'''
from pymodbus.constants import Endian
from pymodbus.interfaces import IPayloadBuilder
from pymodbus.utilities import pack_bitstring
from pymodbus.utilities import unpack_bitstring
from pymodbus.exceptions import ParameterException


class BcdPayloadBuilder(IPayloadBuilder):
    '''
    A utility that helps build binary coded decimal payload
    messages to be written with the various modbus messages.
    example::

        builder = BcdPayloadBuilder()
        builder.add_8bit_uint(1)
        builder.add_16bit_uint(2)
        payload = builder.build()
    '''

    def __init__(self, payload=None):
        ''' Initialize a new instance of the payload builder

        :param payload: Raw payload data to initialize with
        '''
        self._payload = payload or []

    def __str__(self):
        ''' Return the payload buffer as a string

        :returns: The payload buffer as a string
        '''
        return ''.join(self._payload)

    def reset(self):
        ''' Reset the payload buffer
        '''
        self._payload = []

    def build(self):
        ''' Return the payload buffer as a list

        This list is two bytes per element and can
        thus be treated as a list of registers.

        :returns: The payload buffer as a list
        '''
        return str(self)

    def add_bits(self, values):
        ''' Adds a collection of bits to be encoded

        If these are less than a multiple of eight,
        they will be left padded with 0 bits to make
        it so.

        :param value: The value to add to the buffer
        '''
        value = pack_bitstring(values)
        self._payload.append(str(value))

    def add_number(self, value, size=None):
        ''' Adds any numeric type to the buffer

        :param value: The value to add to the buffer
        '''
        value = str(value)
        if size != None:
            length = len(value) - size
            value  = (('0' * length) + value)[0:size]
        self._payload.append(value)

    def add_string(self, value):
        ''' Adds a string to the buffer

        :param value: The value to add to the buffer
        '''
        self._payload.append(value)


class BcdPayloadDecoder(object):
    '''
    A utility that helps decode binary coded decimal payload
    messages from a modbus reponse message. What follows is
    a simple example::

        decoder = BcdPayloadDecoder(payload)
        first   = decoder.decode_8bit_uint()
        second  = decoder.decode_16bit_uint()
    '''

    def __init__(self, payload):
        ''' Initialize a new payload decoder

        :param payload: The payload to decode with
        '''
        self._payload = payload
        self._pointer = 0x00

    @staticmethod
    def fromRegisters(registers, endian=Endian.Little):
        ''' Initialize a payload decoder with the result of
        reading a collection of registers from a modbus device.

        The registers are treated as a list of 2 byte values.
        We have to do this because of how the data has already
        been decoded by the rest of the library.

        :param registers: The register results to initialize with
        :param endian: The endianess of the payload
        :returns: An initialized PayloadDecoder
        '''
        if isinstance(registers, list): # repack into flat binary
            payload = ''.join(pack('>H', x) for x in registers)
            return BinaryPayloadDecoder(payload, endian)
        raise ParameterException('Invalid collection of registers supplied')

    @staticmethod
    def fromCoils(coils, endian=Endian.Little):
        ''' Initialize a payload decoder with the result of
        reading a collection of coils from a modbus device.

        The coils are treated as a list of bit(boolean) values.

        :param coils: The coil results to initialize with
        :param endian: The endianess of the payload
        :returns: An initialized PayloadDecoder
        '''
        if isinstance(coils, list):
            payload = pack_bitstring(coils)
            return BinaryPayloadDecoder(payload, endian)
        raise ParameterException('Invalid collection of coils supplied')

    def reset(self):
        ''' Reset the decoder pointer back to the start
        '''
        self._pointer = 0x00

    def decode_int(self, size=1):
        ''' Decodes a int or long from the buffer
        '''
        self._pointer += size
        handle = self._payload[self._pointer - size:self._pointer]
        return int(handle)

    def decode_float(self, size=1):
        ''' Decodes a floating point number from the buffer
        '''
        self._pointer += size
        handle = self._payload[self._pointer - size:self._pointer]
        return float(handle)

    def decode_bits(self):
        ''' Decodes a byte worth of bits from the buffer
        '''
        self._pointer += 1
        handle = self._payload[self._pointer - 1:self._pointer]
        return unpack_bitstring(handle)

    def decode_string(self, size=1):
        ''' Decodes a string from the buffer

        :param size: The size of the string to decode
        '''
        self._pointer += size
        return self._payload[self._pointer - size:self._pointer]

#---------------------------------------------------------------------------#
# Exported Identifiers
#---------------------------------------------------------------------------#
__all__ = ["BcdPayloadBuilder", "BcdPayloadDecoder"]
