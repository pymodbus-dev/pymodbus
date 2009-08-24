'''
Diagnostic record read/write

Currently not all implemented
'''
import struct
from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.device import ModbusControlBlock

_MCB = ModbusControlBlock()

#---------------------------------------------------------------------------#
# TODO
# - Make these only work on serial
#---------------------------------------------------------------------------#
class ReadExceptionStatusRequest(ModbusRequest):
    '''
    This function code is used to read the contents of eight Exception Status
    outputs in a remote device.  The function provides a simple method for
    accessing this information, because the Exception Output references are
    known (no output reference is needed in the function).
    '''
    function_code = 0x07

    def __init__(self):
        ''' Initializes a new instance
        '''
        ModbusRequest.__init__(self)

    def execute(self):
        ''' Run a read exeception status request against the store

        :returns: The populated response
        '''
        status = _MCB.getCounterSummary()
        return ReadExceptionStatusResponse(status)

class ReadExceptionStatusResponse(ModbusResponse):
    '''
    The normal response contains the status of the eight Exception Status
    outputs. The outputs are packed into one data byte, with one bit
    per output. The status of the lowest output reference is contained
    in the least significant bit of the byte.  The contents of the eight
    Exception Status outputs are device specific.
    '''
    function_code = 0x07

    def __init__(self, status):
        ''' Initializes a new instance

        :param status: The status response to report
        '''
        ModbusRequest.__init__(self)
        self.status = status

    def encode(self):
        ''' Encodes the response

        :returns: The byte encoded message
        '''
        return struct.pack('>B', self.status)

    def decode(self, data):
        ''' Decodes a the response

        :param data: The packet data to decode
        '''
        self.status = struct.unpack('>B', data)


# Encapsulate interface transport 43, 14
# CANopen general reference 43, 13

#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
# get com event counter 11

#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
# get com event log 12

#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
# report slave id 17

#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
# report device identification 43, 14

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ReadExceptionStatusRequest",
    "ReadExceptionStatusResponse"
]
