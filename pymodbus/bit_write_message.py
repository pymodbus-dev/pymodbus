"""
Bit Writing Request/Response
------------------------------

TODO write mask request/response
"""
import struct
from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.utilities import *

#---------------------------------------------------------------------------#
# Local Constants
#---------------------------------------------------------------------------#
# These are defined in the spec to turn a coil on/off
#---------------------------------------------------------------------------#
_turn_coil_on   = struct.pack(">BB", 0xff, 0x00)
_turn_coil_off  = struct.pack(">BB", 0x00, 0x00)

class WriteSingleCoilRequest(ModbusRequest):
    '''
    This function code is used to write a single output to either ON or OFF
    in a remote device.

    The requested ON/OFF state is specified by a constant in the request
    data field. A value of FF 00 hex requests the output to be ON. A value
    of 00 00 requests it to be OFF. All other values are illegal and will
    not affect the output.

    The Request PDU specifies the address of the coil to be forced. Coils
    are addressed starting at zero. Therefore coil numbered 1 is addressed
    as 0. The requested ON/OFF state is specified by a constant in the Coil
    Value field. A value of 0XFF00 requests the coil to be ON. A value of
    0X0000 requests the coil to be off. All other values are illegal and
    will not affect the coil.
    '''
    function_code = 5

    def __init__(self, address=None, value=None):
        ''' Initializes a new instance

        :param address: The variable address to write
        :param value: The value to write at address
        '''
        ModbusRequest.__init__(self)
        self.address = address
        self.value = 0xff00 if value else 0x0000

    def encode(self):
        ''' Encodes write coil request

        :returns: The byte encoded message
        '''
        result  = struct.pack('>H', self.address)
        result += _turn_coil_on if self.value else _turn_coil_off
        return result

    def decode(self, data):
        ''' Decodes a write coil request

        :param data: The packet data to decode
        '''
        self.address, self.value = struct.unpack('>HH', data)

    def execute(self, context):
        ''' Run a write coil request against a datastore

        :param context: The datastore to request from
        :returns: The populated response or exception message
        '''
        if self.value != 0 and self.value != 0xff00:
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address):
            return self.doException(merror.IllegalAddress)
        context.setValues(self.function_code, self.address, [self.value == 0xff00])
        values = context.getValues(self.function_code, self.address)
        return WriteSingleCoilResponse(self.address, values[0])

    def __str__(self):
        ''' Returns a string representation of the instance

        :return: A string representation of the instance
        '''
        return "WriteCoilRequest(%d)" % self.address, self.value

class WriteSingleCoilResponse(ModbusResponse):
    '''
    The normal response is an echo of the request, returned after the coil
    state has been written.
    '''
    function_code = 5

    def __init__(self, address=None, value=None):
        ''' Initializes a new instance

        :param address: The variable address written to
        :param value: The value written at address
        '''
        ModbusResponse.__init__(self)
        self.address = address
        self.value = value

    def encode(self):
        ''' Encodes write coil response

        :return: The byte encoded message
        '''
        result  = struct.pack('>H', self.address)
        result += _turn_coil_on if self.value else _turn_coil_off
        return result

    def decode(self, data):
        ''' Decodes a write coil response

        :param data: The packet data to decode
        '''
        self.address, value = struct.unpack('>HH', data)
        self.value = (value != 0)

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "WriteCoilResponse(%d)" % self.address, self.value

#---------------------------------------------------------------------------#
# TODO Fix this so we can write more than false to multiple variables
#---------------------------------------------------------------------------#
class WriteMultipleCoilsRequest(ModbusRequest):
    '''
    "This function code is used to force each coil in a sequence of coils to
    either ON or OFF in a remote device. The Request PDU specifies the coil
    references to be forced. Coils are addressed starting at zero. Therefore
    coil numbered 1 is addressed as 0.

    The requested ON/OFF states are specified by contents of the request
    data field. A logical '1' in a bit position of the field requests the
    corresponding output to be ON. A logical '0' requests it to be OFF."
    '''
    function_code = 15

    def __init__(self, address=None, count=None):
        ''' Initializes a new instance

        :param address: The starting request address
        :param count: Number of bits to read after address
        '''
        ModbusRequest.__init__(self)
        self.address = address
        if count != None and count > 0:
            self.coils = [False] * count
        else: self.coils = []

    def encode(self):
        ''' Encodes write coils request

        :returns: The byte encoded message
        '''
        count = len(self.coils)
        result  = struct.pack('>HHB', self.address, count, (count + 7) / 8)
        result += packBitsToString(self.coils)
        return result

    def decode(self, data):
        ''' Decodes a write coils request

        :param data: The packet data to decode
        '''
        self.address, count = struct.pack('>HH', data[0:2])
        coils, self.byte_count = unpackBitsFromString(data[2:])
        self.coils = coils[:count]

    def execute(self, context):
        ''' Run a write coils request against a datastore

        :param context: The datastore to request from
        :returns: The populated response or exception message
        '''
        count = len(self.coils)
        if not (1 <= count <= 0x07b0):
            return self.createExceptionResponse(merror.IllegalValue)
        if (self.byte_count != (count + 7) / 8):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, count):
            return self.doException(merror.IllegalAddress)
        context.setValues(self.function_code, self.address, self.coils)
        return WriteMultipleCoilsResponse(self.address, count)

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "WriteNCoilRequest %d => " % self.address, self.coils

class WriteMultipleCoilsResponse(ModbusResponse):
    '''
    The normal response returns the function code, starting address, and
    quantity of coils forced.
    '''
    function_code = 15

    def __init__(self, address=None, count=None):
        ''' Initializes a new instance

        :param address: The starting variable address written to
        :param count: The number of values written
        '''
        ModbusResponse.__init__(self)
        self.address = address
        self.count = count

    def encode(self):
        ''' Encodes write coils response

        :returns: The byte encoded message
        '''
        return struct.pack('>HH', self.address, self.count)

    def decode(self, data):
        ''' Decodes a write coils response

        :param data: The packet data to decode
        '''
        self.address, self.count = struct.unpack('>HH', data)

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "WriteNCoilResponse(%d,%d)" % (self.address, self.count)

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "WriteSingleCoilRequest", "WriteSingleCoilResponse",
    "WriteMultipleCoilsRequest", "WriteMultipleCoilsResponse",
]
