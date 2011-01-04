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

class EventStatus(object):
    '''
    '''
    Waiting = 0xffff
    Ready   = 0x0000

#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
class GetCommEventCounterRequest(ModbusRequest):
    '''
    This function code is used to get a status word and an event count from the
    remote device's communication event counter. 

    By fetching the current count before and after a series of messages, a client
    can determine whether the messages were handled normally by the remote device. 

    The device's event counter is incremented once  for each successful message
    completion. It is not incremented for exception responses, poll commands,
    or fetch event counter commands. 

    The event counter can be reset by means of the Diagnostics function (code 08),
    with a subfunction of Restart Communications Option (code 00 01) or
    Clear Counters and Diagnostic Register (code 00 0A).
    '''
    function_code = 0x0b

    def __init__(self):
        ''' Initializes a new instance
        '''
        ModbusRequest.__init__(self)

    def execute(self):
        ''' Run a read exeception status request against the store

        :returns: The populated response
        '''
        status = _MCB.BusMessage
        return GetCommEventCounterResponseResponse(status)

class GetCommEventCounterResponse(ModbusResponse):
    '''
    The normal response contains a two-byte status word, and a two-byte
    event count. The status word will be all ones (FF FF hex) if a
    previously-issued program command is still being processed by the remote
    device (a busy condition exists). Otherwise, the status word will be 
    all zeros.
    '''
    function_code = 0x0b

    def __init__(self, count):
        ''' Initializes a new instance

        :param count: The current event counter value
        '''
        ModbusRequest.__init__(self)
        self.count = count
        self.status = True # this means we are ready, not waiting

    def encode(self):
        ''' Encodes the response

        :returns: The byte encoded message
        '''
        ready = EventStatus.Ready if self.status else EventStatus.Waiting
        return struct.pack('>HH', ready, self.count)

    def decode(self, data):
        ''' Decodes a the response

        :param data: The packet data to decode
        '''
        ready, self.count = struct.unpack('>HH', data)
        self.status = (ready == EventStatus.Ready)

#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
# get com event log 12

#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
class ReportSlaveIdRequest(ModbusRequest):
    '''
    This function code is used to read the description of the type, the current
    status, and other information specific to a remote device. 
    '''
    function_code = 0x11

    def __init__(self):
        ''' Initializes a new instance
        '''
        ModbusRequest.__init__(self)

    def execute(self):
        ''' Run a read exeception status request against the store

        :returns: The populated response
        '''
        status = _MCB.getCounterSummary()
        return ReportSlaveIdResponse(status)

class ReportSlaveIdResponse(ModbusResponse):
    '''
    The format of a normal response is shown in the following example. The
    data contents are specific to each type of device.
    '''
    function_code = 0x11

    def __init__(self, identifier, status=True):
        ''' Initializes a new instance

        :param identifier: The identifier of the slave
        :param status: The status response to report
        '''
        ModbusRequest.__init__(self)
        self.identifier = identifier
        self.status = status

    def encode(self):
        ''' Encodes the response

        :returns: The byte encoded message
        '''
        status = 0xFF if self.status else 0x00
        return struct.pack('>BBB', 0x03, self.identifier, self.status)

    def decode(self, data):
        ''' Decodes a the response

        :param data: The packet data to decode
        '''
        length, self.identifier, status = struct.unpack('>BBB', data)
        self.status = status == 0xFF

#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
# report device identification 43, 14

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ReadExceptionStatusRequest", "ReadExceptionStatusResponse"
    "ReportSlaveIdRequest", "ReportSlaveIdResponse",
]
