'''
Diagnostic record read/write

Currently not implemented
'''

from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
import struct

#---------------------------------------------------------------------------#
# TODO
# - Make these only work on serial
# - Link the execute with the server context
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
        ModbusRequest.__init__(self)

    def execute(self, status):
        #if cannot_read_status:
        #       return self.doException(merror.SlaveFailure)
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
        ModbusRequest.__init__(self)
        self.status = status

    def encode(self):
        ret = struct.pack('>B', self.status)
        return ret

    def decode(self, data):
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

#__all__ = []
