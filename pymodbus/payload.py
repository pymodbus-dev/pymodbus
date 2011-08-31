'''
Modbus Payload Builders
------------------------

A collection of utilities for building and decoding
modbus messages payloads.
'''
from struct import pack, unpack
from pymodbus.constants import Endian


class PayloadBuilder(object):

    def __init__(self, payload=None, endian=Endian.Big):
        ''' Initialize a new instance of the payload builder

        :param payload: Raw payload data to initialize with
        :param endian: The endianess of the payload
        '''
        self.payload = payload or []

    def reset(self):
        ''' Reset the payload buffer
        '''
        self.payload = []

    def tostring(self):
        ''' Return the payload buffer as a string

        :returns: The payload buffer as a string
        '''
        return ''.join(self.payload)

    def tolist(self):
        ''' Return the payload buffer as a list

        :returns: The payload buffer as a list
        '''
        return self.payload

    def add_8bit_uint(self, value):
        ''' Adds a 8 bit unsigned int to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('B', value))

    def add_16bit_uint(self, value):
        ''' Adds a 16 bit unsigned int to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('H', value))

    def add_32bit_uint(self, value):
        ''' Adds a 32 bit unsigned int to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('I', value))

    def add_64bit_uint(self, value):
        ''' Adds a 64 bit unsigned int to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('Q', value))

    def add_8bit_int(self, value):
        ''' Adds a 8 bit signed int to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('b', value))

    def add_16bit_int(self, value):
        ''' Adds a 16 bit signed int to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('h', value))

    def add_32bit_int(self, value):
        ''' Adds a 32 bit signed int to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('i', value))

    def add_64bit_int(self, value):
        ''' Adds a 64 bit signed int to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('q', value))

    def add_32bit_float(self, value):
        ''' Adds a 32 bit float to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('f', value))

    def add_64bit_float(self, value):
        ''' Adds a 64 bit float(double) to the buffer

        :param value: The value to add to the buffer
        '''
        self.payload.append(pack('d', value))
            
    def add_string(self, value):
        ''' Adds a string to the buffer

        :param value: The value to add to the buffer
        '''
        for c in value:
            self.payload.append(pack('s', c))


class PayloadDecoder(object):

    def __init__(self, payload, endian=Endian.Big):
        ''' Initialize a new payload decoder

        :param payload: The payload to decode with
        :param endian: The endianess of the payload
        '''
        self.payload = payload
        self.pointer = 0x00

    def reset(self):
        ''' Reset the decoder pointer back to the start
        '''
        self.pointer = 0x00

    def decode_8bit_uint(self):
        ''' Decodes a 8 bit unsigned int from the buffer
        '''
        self.pointer += 1
        return unpack('B', self.payload[self.pointer - 1:self.pointer])[0]

    def decode_16bit_uint(self):
        ''' Decodes a 16 bit unsigned int from the buffer
        '''
        self.pointer += 2
        return unpack('H', self.payload[self.pointer - 2:self.pointer])[0]

    def decode_32bit_uint(self):
        ''' Decodes a 32 bit unsigned int from the buffer
        '''
        self.pointer += 4
        return unpack('I', self.payload[self.pointer - 4:self.pointer])[0]

    def decode_64bit_uint(self):
        ''' Decodes a 64 bit unsigned int from the buffer
        '''
        self.pointer += 8
        return unpack('Q', self.payload[self.pointer - 8:self.pointer])[0]

    def decode_8bit_int(self):
        ''' Decodes a 8 bit signed int from the buffer
        '''
        self.pointer += 1
        return unpack('b', self.payload[self.pointer - 1:self.pointer])[0]

    def decode_16bit_int(self):
        ''' Decodes a 16 bit signed int from the buffer
        '''
        self.pointer += 2
        return unpack('h', self.payload[self.pointer - 2:self.pointer])[0]

    def decode_32bit_int(self):
        ''' Decodes a 32 bit signed int from the buffer
        '''
        self.pointer += 4
        return unpack('i', self.payload[self.pointer - 4:self.pointer])[0]

    def decode_64bit_int(self):
        ''' Decodes a 64 bit signed int from the buffer
        '''
        self.pointer += 8
        return unpack('q', self.payload[self.pointer - 8:self.pointer])[0]

    def decode_32bit_float(self):
        ''' Decodes a 32 bit float from the buffer
        '''
        self.pointer += 4
        return unpack('f', self.payload[self.pointer - 4:self.pointer])[0]

    def decode_64bit_float(self):
        ''' Decodes a 64 bit float(double) from the buffer
        '''
        self.pointer += 8
        return unpack('d', self.payload[self.pointer - 8:self.pointer])[0]
            
    def decode_string(self, size=1):
        ''' Decodes a string from the buffer

        :param size: The size of the string to decode
        '''
        self.pointer += size
        return self.payload[self.pointer - size:self.pointer]

#---------------------------------------------------------------------------#
# Exported Identifiers
#---------------------------------------------------------------------------#
__all__ = ["PayloadBuilder", "PayloadDecoder"]
