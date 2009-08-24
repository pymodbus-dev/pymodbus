'''
Diagnostic Record Read/Write
------------------------------

These need to be tied into a the current server context
or linked to the appropriate data
'''
import struct

from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.device import ModbusControlBlock
from pymodbus.mexceptions import NotImplementedException
from pymodbus.utilities import packBitsToString

_MCB = ModbusControlBlock()

#---------------------------------------------------------------------------#
# Diagnostic Function Codes Base Classes
# diagnostic 08, 00-18,20
#---------------------------------------------------------------------------#
# TODO Make these only work on serial
#---------------------------------------------------------------------------#
class DiagnosticStatusRequest(ModbusRequest):
    '''
    This is a base class for all of the diagnostic request functions
    '''
    function_code = 0x08

    def __init__(self):
        '''
        Base initializer for a diagnostic request
        '''
        ModbusRequest.__init__(self)

    def encode(self):
        '''
        Base encoder for a diagnostic response
        we encode the data set in self.message

        :returns: The encoded packet
        '''
        ret = struct.pack('>H', self.sub_function_code)
        if self.message is not None:
            if isinstance(self.message, str):
                ret += self.message
            elif isinstance(self.message, list):
                for r in self.message:
                    ret += struct.pack('>H', r)
            elif isinstance(self.message, int):
                ret += struct.pack('>H', self.message)
        return ret

    def decode(self, data):
        ''' Base decoder for a diagnostic request

        :param data: The data to decode into the function code
        '''
        self.sub_function_code, self.message = struct.unpack('>HH', data)

class DiagnosticStatusResponse(ModbusResponse):
    '''
    This is a base class for all of the diagnostic response functions

    It works by performing all of the encoding and decoding of variable
    data and lets the higher classes define what extra data to append
    and how to execute a request
    '''
    function_code = 0x08

    def __init__(self):
        '''
        Base initializer for a diagnostic response
        '''
        ModbusResponse.__init__(self)

    def encode(self):
        '''
        Base encoder for a diagnostic response
        we encode the data set in self.message

        :returns: The encoded packet
        '''
        ret = struct.pack('>H', self.sub_function_code)
        if self.message is not None:
            if isinstance(self.message, str):
                ret += self.message
            elif isinstance(self.message, list):
                for r in self.message:
                    ret += struct.pack('>H', r)
            elif isinstance(self.message, int):
                ret += struct.pack('>H', self.message)
        return ret

    def decode(self, data):
        ''' Base decoder for a diagnostic response
        :param data: The data to decode into the function code
        '''
        self.sub_function_code, self.message = struct.unpack('>HH', data)

class DiagnosticStatusSimpleRequest(DiagnosticStatusRequest):
    '''
    A large majority of the diagnostic functions are simple
    status request functions.  They work by sending 0x0000
    as data and their function code and they are returned
    2 bytes of data.

    If a function inherits this, they only need to implement
    the execute method
    '''

    def __init__(self, data=0x0000):
        '''
        General initializer for a simple diagnostic request

        The data defaults to 0x0000 if not provided as over half
        of the functions require it.

        :param data: The data to send along with the request
        '''
        DiagnosticStatusRequest.__init__(self)
        self.message = data

    def execute(self):
        ''' Base function to raise if not implemented '''
        raise NotImplementedException("Diagnostic Message Has No Execute Method")

class DiagnosticStatusSimpleResponse(DiagnosticStatusResponse):
    '''
    A large majority of the diagnostic functions are simple
    status request functions.  They work by sending 0x0000
    as data and their function code and they are returned
    2 bytes of data.
    '''

    def __init__(self, data):
        ''' General initializer for a simple diagnostic response

        :param data: The resulting data to return to the client
        '''
        DiagnosticStatusResponse.__init__(self)
        self.message = data

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 00
#---------------------------------------------------------------------------#
class ReturnQueryDataRequest(DiagnosticStatusRequest):
    '''
    The data passed in the request data field is to be returned (looped back)
    in the response. The entire response message should be identical to the
    request.
    '''
    sub_function_code = 0x0000

    def __init__(self, message):
        ''' Initializes a new instance of the request

        :param message: The message to send to loopback
        '''
        DiagnosticStatusRequest.__init__(self)
        if isinstance(message, list):
            self.message = message
        else: self.message = [message]

    def execute(self):
        ''' Executes the loopback request (builds the response)

        :returns: The populated loopback response message
        '''
        return ReturnQueryDataResponse(self.message)

class ReturnQueryDataResponse(DiagnosticStatusResponse):
    '''
    The data passed in the request data field is to be returned (looped back)
    in the response. The entire response message should be identical to the
    request.
    '''
    sub_function_code = 0x0000

    def __init__(self, message):
        ''' Initializes a new instance of the response

        :param message: The message to loopback
        '''
        DiagnosticStatusResponse.__init__(self)
        if isinstance(message, list):
            self.message = message
        else: self.message = [message]

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 01
#---------------------------------------------------------------------------#
class RestartCommunicationsOptionRequest(DiagnosticStatusRequest):
    '''
    The remote device serial line port must be initialized and restarted, and
    all of its communications event counters are cleared. If the port is
    currently in Listen Only Mode, no response is returned. This function is
    the only one that brings the port out of Listen Only Mode. If the port is
    not currently in Listen Only Mode, a normal response is returned. This
    occurs before the restart is executed.
    '''
    sub_function_code = 0x0001

    def __init__(self, toggle=False):
        DiagnosticStatusRequest.__init__(self)
        if toggle:
            self.message = [0xff00]
        else: self.message = [0x0000]

    def execute(self):
        ''' Clear event log and restart

        :returns: The initialized response message
        '''
        #if _MCB.ListenOnly:
        return RestartCommunicationsOptionResponse(self.message)

class RestartCommunicationsOptionResponse(DiagnosticStatusResponse):
    '''
    The remote device serial line port must be initialized and restarted, and
    all of its communications event counters are cleared. If the port is
    currently in Listen Only Mode, no response is returned. This function is
    the only one that brings the port out of Listen Only Mode. If the port is
    not currently in Listen Only Mode, a normal response is returned. This
    occurs before the restart is executed.
    '''
    sub_function_code = 0x0001

    def __init__(self, toggle=False):
        ''' Initializes a new response

        :param toggle: Set to True if we toggled, False otherwise
        '''
        DiagnosticStatusResponse.__init__(self)
        if toggle:
            self.message = [0xff00]
        else: self.message = [0x0000]

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 02
#---------------------------------------------------------------------------#
class ReturnDiagnosticRegisterRequest(DiagnosticStatusSimpleRequest):
    '''
    The contents of the remote device's 16-bit diagnostic register are
    returned in the response
    '''
    sub_function_code = 0x0002

    def execute(self):
        #if _MCB.isListenOnly():
        register = packBitsToString(_MCB.getDiagnosticRegister())
        return ReturnDiagnosticRegisterResponse(register)

class ReturnDiagnosticRegisterResponse(DiagnosticStatusSimpleResponse):
    '''
    The contents of the remote device's 16-bit diagnostic register are
    returned in the response
    '''
    sub_function_code = 0x0002

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 03
#---------------------------------------------------------------------------#
class ChangeAsciiInputDelimiterRequest(DiagnosticStatusSimpleRequest):
    '''
    The character 'CHAR' passed in the request data field becomes the end of
    message delimiter for future messages (replacing the default LF
    character). This function is useful in cases of a Line Feed is not
    required at the end of ASCII messages.
    @param data The character to set as the new delimiter
    '''
    sub_function_code = 0x0003

    def execute(self):
        '''
        For future serial messages, use char for delimiter
        '''
        char = (self.message & 0xff00) >> 8
        _MCB.Delimiter = char
        return ChangeAsciiInputDelimiterResponse(self.message)

class ChangeAsciiInputDelimiterResponse(DiagnosticStatusSimpleResponse):
    '''
    The character 'CHAR' passed in the request data field becomes the end of
    message delimiter for future messages (replacing the default LF
    character). This function is useful in cases of a Line Feed is not
    required at the end of ASCII messages.
    '''
    sub_function_code = 0x0003

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 04
#---------------------------------------------------------------------------#
class ForceListenOnlyModeRequest(DiagnosticStatusSimpleRequest):
    '''
    Forces the addressed remote device to its Listen Only Mode for MODBUS
    communications.  This isolates it from the other devices on the network,
    allowing them to continue communicating without interruption from the
    addressed remote device. No response is returned.
    '''
    sub_function_code = 0x0004

    def execute(self):
        _MCB.ListenOnly = not _MCB.ListenOnly
        return ForceListenOnlyModeResponse()

class ForceListenOnlyModeResponse(DiagnosticStatusResponse):
    '''
    Forces the addressed remote device to its Listen Only Mode for MODBUS
    communications.  This isolates it from the other devices on the network,
    allowing them to continue communicating without interruption from the
    addressed remote device. No response is returned.

    This does not send a response
    '''
    sub_function_code = 0x0004

    def __init__(self):
        ''' Initializer to block a return response
        '''
        DiagnosticStatusResponse.__init__(self)
        self.message = []

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 10
#---------------------------------------------------------------------------#
class ClearCountersRequest(DiagnosticStatusSimpleRequest):
    '''
    The goal is to clear ll counters and the diagnostic register.
    Also, counters are cleared upon power-up
    '''
    sub_function_code = 0x000A

    def execute(self):
        '''
        '''
        _MCB.reset()
        return ClearCountersResponse(self.message)

class ClearCountersResponse(DiagnosticStatusSimpleResponse):
    '''
    The goal is to clear ll counters and the diagnostic register.
    Also, counters are cleared upon power-up
    '''
    sub_function_code = 0x000A

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 11
#---------------------------------------------------------------------------#
class ReturnBusMessageCountRequest(DiagnosticStatusSimpleRequest):
    '''
    The response data field returns the quantity of messages that the
    remote device has detected on the communications systems since its last
    restart, clear counters operation, or power-up
    '''
    sub_function_code = 0x000B

    def execute(self):
        '''
        '''
        count = _MCB.Counter.BusMessage
        return ReturnBusMessageCountResponse(count)

class ReturnBusMessageCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of messages that the
    remote device has detected on the communications systems since its last
    restart, clear counters operation, or power-up
    '''
    sub_function_code = 0x000B

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 12
#---------------------------------------------------------------------------#
class ReturnBusCommunicationErrorCountRequest(DiagnosticStatusSimpleRequest):
    '''
    The response data field returns the quantity of CRC errors encountered
    by the remote device since its last restart, clear counter operation, or
    power-up
    '''
    sub_function_code = 0x000C

    def execute(self):
        '''
        '''
        count = _MCB.Counter.BusCommunicationError
        return ReturnBusCommunicationErrorCountResponse(count)

class ReturnBusCommunicationErrorCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of CRC errors encountered
    by the remote device since its last restart, clear counter operation, or
    power-up
    '''
    sub_function_code = 0x000C

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 13
#---------------------------------------------------------------------------#
class ReturnBusExceptionErrorCountRequest(DiagnosticStatusSimpleRequest):
    '''
    The response data field returns the quantity of modbus exception
    responses returned by the remote device since its last restart,
    clear counters operation, or power-up
    '''
    sub_function_code = 0x000D

    def execute(self):
        '''
        '''
        count = _MCB.Counter.BusExceptionError
        return ReturnBusExceptionErrorCountResponse(count)

class ReturnBusExceptionErrorCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of modbus exception
    responses returned by the remote device since its last restart,
    clear counters operation, or power-up
    '''
    sub_function_code = 0x000D

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 14
#---------------------------------------------------------------------------#
class ReturnSlaveMessageCountRequest(DiagnosticStatusSimpleRequest):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device, or broadcast, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    '''
    sub_function_code = 0x000E

    def execute(self):
        '''
        '''
        count = _MCB.Counter.SlaveMessage
        return ReturnSlaveMessageCountResponse(count)

class ReturnSlaveMessageCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device, or broadcast, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    '''
    sub_function_code = 0x000E

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 15
#---------------------------------------------------------------------------#
class ReturnSlaveNoResponseCountRequest(DiagnosticStatusSimpleRequest):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device, or broadcast, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    '''
    sub_function_code = 0x000F

    def execute(self):
        '''
        '''
        count = _MCB.Counter.SlaveNoResponse
        return ReturnSlaveNoReponseCountResponse(count)

class ReturnSlaveNoReponseCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device, or broadcast, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    '''
    sub_function_code = 0x000F

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 16
#---------------------------------------------------------------------------#
class ReturnSlaveNAKCountRequest(DiagnosticStatusSimpleRequest):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Negative Acknowledge (NAK) exception
    response, since its last restart, clear counters operation, or power-up.
    Exception responses are described and listed in section 7 .
    '''
    sub_function_code = 0x0010

    def execute(self):
        '''
        '''
        count = _MCB.Counter.SlaveNAK
        return ReturnSlaveNAKCountResponse(count)

class ReturnSlaveNAKCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Negative Acknowledge (NAK) exception
    response, since its last restart, clear counters operation, or power-up.
    Exception responses are described and listed in section 7.
    '''
    sub_function_code = 0x0010

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 17
#---------------------------------------------------------------------------#
class ReturnSlaveBusyCountRequest(DiagnosticStatusSimpleRequest):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Slave Device Busy exception response,
    since its last restart, clear counters operation, or power-up.
    '''
    sub_function_code = 0x0011

    def execute(self):
        '''
        '''
        count = _MCB.Counter.SlaveBusy
        return ReturnSlaveBusyCountResponse(count)

class ReturnSlaveBusyCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Slave Device Busy exception response,
    since its last restart, clear counters operation, or power-up.
    '''
    sub_function_code = 0x0011

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 18
#---------------------------------------------------------------------------#
class ReturnSlaveBusCharacterOverrunCountRequest(DiagnosticStatusSimpleRequest):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device that it could not handle due to a character overrun condition,
    since its last restart, clear counters operation, or power-up. A character
    overrun is caused by data characters arriving at the port faster than they
    can be stored, or by the loss of a character due to a hardware malfunction.
    '''
    sub_function_code = 0x0012

    def execute(self):
        '''
        '''
        count = _MCB.Counter.BusCharacterOverrun
        return ReturnSlaveBusCharacterOverrunCountResponse(count)

class ReturnSlaveBusCharacterOverrunCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of messages addressed to the
    remote device that it could not handle due to a character overrun condition,
    since its last restart, clear counters operation, or power-up. A character
    overrun is caused by data characters arriving at the port faster than they
    can be stored, or by the loss of a character due to a hardware malfunction.
    '''
    sub_function_code = 0x0012

#---------------------------------------------------------------------------#
# Diagnostic Sub Code 20
#---------------------------------------------------------------------------#
class ClearOverrunCountRequest(DiagnosticStatusSimpleRequest):
    '''
    Clears the overrun error counter and reset the error flag
    '''
    sub_function_code = 0x0014

    def execute(self):
        '''
        '''
        _MCB.Counter.BusCharacterOverrun = 0x0000
        # clear error register
        return ClearOverrunCountResponse(self.message)

class ClearOverrunCountResponse(DiagnosticStatusSimpleResponse):
    '''
    Clears the overrun error counter and reset the error flag
    '''
    sub_function_code = 0x0014

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ReturnQueryDataRequest", "ReturnQueryDataResponse",
    "RestartCommunicationsOptionRequest", "RestartCommunicationsOptionResponse",
    "ReturnDiagnosticRegisterRequest", "ReturnDiagnosticRegisterResponse",
    "ChangeAsciiInputDelimiterRequest", "ChangeAsciiInputDelimiterResponse",
    "ForceListenOnlyModeRequest", "ForceListenOnlyModeResponse",
    "ClearCountersRequest", "ClearCountersResponse",
    "ReturnBusMessageCountRequest", "ReturnBusMessageCountResponse",
    "ReturnBusCommunicationErrorCountRequest", "ReturnBusCommunicationErrorCountResponse",
    "ReturnBusExceptionErrorCountRequest", "ReturnBusExceptionErrorCountResponse",
    "ReturnSlaveMessageCountRequest", "ReturnSlaveMessageCountResponse",
    "ReturnSlaveNoResponseCountRequest", "ReturnSlaveNoReponseCountResponse",
    "ReturnSlaveNAKCountRequest", "ReturnSlaveNAKCountResponse",
    "ReturnSlaveBusyCountRequest", "ReturnSlaveBusyCountResponse",
    "ReturnSlaveBusCharacterOverrunCountRequest", "ReturnSlaveBusCharacterOverrunCountResponse",
    "ClearOverrunCountRequest", "ClearOverrunCountResponse",
]
