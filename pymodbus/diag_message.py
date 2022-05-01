'''
Diagnostic Record Read/Write
------------------------------

These need to be tied into a the current server context
or linked to the appropriate data
'''
import struct

from pymodbus.constants import ModbusStatus, ModbusPlusOperation
from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.device import ModbusControlBlock
from pymodbus.exceptions import NotImplementedException
from pymodbus.utilities import pack_bitstring

_MCB = ModbusControlBlock()


#---------------------------------------------------------------------------#
# Diagnostic Function Codes Base Classes
# diagnostic 08, 00-18,20
#---------------------------------------------------------------------------#
# TODO Make sure all the data is decoded from the response
#---------------------------------------------------------------------------#
class DiagnosticStatusRequest(ModbusRequest):
    '''
    This is a base class for all of the diagnostic request functions
    '''
    function_code = 0x08
    _rtu_frame_size = 8

    def __init__(self, **kwargs):
        '''
        Base initializer for a diagnostic request
        '''
        ModbusRequest.__init__(self, **kwargs)
        self.message = None

    def encode(self):
        '''
        Base encoder for a diagnostic response
        we encode the data set in self.message

        :returns: The encoded packet
        '''
        packet = struct.pack('>H', self.sub_function_code)
        if self.message is not None:
            if isinstance(self.message, str):
                packet += self.message.encode()
            elif isinstance(self.message, bytes):
                packet += self.message
            elif isinstance(self.message, list):
                for piece in self.message:
                    packet += struct.pack('>H', piece)
            elif isinstance(self.message, int):
                packet += struct.pack('>H', self.message)
        return packet

    def decode(self, data):
        ''' Base decoder for a diagnostic request

        :param data: The data to decode into the function code
        '''
        self.sub_function_code, self.message = struct.unpack('>HH', data)
    
    def get_response_pdu_size(self):
        """
        Func_code (1 byte) + Sub function code (2 byte) + Data (2 * N bytes)
        :return: 
        """
        if not isinstance(self.message,list):
            self.message = [self.message]
        return 1 + 2 + 2 * len(self.message)


class DiagnosticStatusResponse(ModbusResponse):
    '''
    This is a base class for all of the diagnostic response functions

    It works by performing all of the encoding and decoding of variable
    data and lets the higher classes define what extra data to append
    and how to execute a request
    '''
    function_code = 0x08
    _rtu_frame_size = 8

    def __init__(self, **kwargs):
        '''
        Base initializer for a diagnostic response
        '''
        ModbusResponse.__init__(self, **kwargs)
        self.message = None

    def encode(self):
        '''
        Base encoder for a diagnostic response
        we encode the data set in self.message

        :returns: The encoded packet
        '''
        packet = struct.pack('>H', self.sub_function_code)
        if self.message is not None:
            if isinstance(self.message, str):
                packet += self.message.encode()
            elif isinstance(self.message, bytes):
                packet += self.message
            elif isinstance(self.message, list):
                for piece in self.message:
                    packet += struct.pack('>H', piece)
            elif isinstance(self.message, int):
                packet += struct.pack('>H', self.message)
        return packet

    def decode(self, data):
        ''' Base decoder for a diagnostic response

        :param data: The data to decode into the function code
        '''
        word_len = len(data)//2
        if len(data) % 2:
            word_len += 1
            data = data + b'0'
        data = struct.unpack('>' + 'H'*word_len, data)
        self.sub_function_code, self.message = data[0], data[1:]


class DiagnosticStatusSimpleRequest(DiagnosticStatusRequest):
    '''
    A large majority of the diagnostic functions are simple
    status request functions.  They work by sending 0x0000
    as data and their function code and they are returned
    2 bytes of data.

    If a function inherits this, they only need to implement
    the execute method
    '''

    def __init__(self, data=0x0000, **kwargs):
        '''
        General initializer for a simple diagnostic request

        The data defaults to 0x0000 if not provided as over half
        of the functions require it.

        :param data: The data to send along with the request
        '''
        DiagnosticStatusRequest.__init__(self, **kwargs)
        self.message = data

    def execute(self, *args):
        ''' Base function to raise if not implemented '''
        raise NotImplementedException("Diagnostic Message Has No Execute Method")


class DiagnosticStatusSimpleResponse(DiagnosticStatusResponse):
    '''
    A large majority of the diagnostic functions are simple
    status request functions.  They work by sending 0x0000
    as data and their function code and they are returned
    2 bytes of data.
    '''

    def __init__(self, data=0x0000, **kwargs):
        ''' General initializer for a simple diagnostic response

        :param data: The resulting data to return to the client
        '''
        DiagnosticStatusResponse.__init__(self, **kwargs)
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

    def __init__(self, message=0x0000, **kwargs):
        ''' Initializes a new instance of the request

        :param message: The message to send to loopback
        '''
        DiagnosticStatusRequest.__init__(self, **kwargs)
        if isinstance(message, list):
            self.message = message
        else:
            self.message = [message]

    def execute(self, *args):
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

    def __init__(self, message=0x0000, **kwargs):
        ''' Initializes a new instance of the response

        :param message: The message to loopback
        '''
        DiagnosticStatusResponse.__init__(self, **kwargs)
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

    def __init__(self, toggle=False, **kwargs):
        ''' Initializes a new request

        :param toggle: Set to True to toggle, False otherwise
        '''
        DiagnosticStatusRequest.__init__(self, **kwargs)
        if toggle:
            self.message   = [ModbusStatus.On]
        else: self.message = [ModbusStatus.Off]

    def execute(self, *args):
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

    def __init__(self, toggle=False, **kwargs):
        ''' Initializes a new response

        :param toggle: Set to True if we toggled, False otherwise
        '''
        DiagnosticStatusResponse.__init__(self, **kwargs)
        if toggle:
            self.message   = [ModbusStatus.On]
        else: self.message = [ModbusStatus.Off]


#---------------------------------------------------------------------------#
# Diagnostic Sub Code 02
#---------------------------------------------------------------------------#
class ReturnDiagnosticRegisterRequest(DiagnosticStatusSimpleRequest):
    '''
    The contents of the remote device's 16-bit diagnostic register are
    returned in the response
    '''
    sub_function_code = 0x0002

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
        '''
        #if _MCB.isListenOnly():
        register = pack_bitstring(_MCB.getDiagnosticRegister())
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
    '''
    sub_function_code = 0x0003

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
        '''
        _MCB.ListenOnly = True
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
    should_respond    = False

    def __init__(self, **kwargs):
        ''' Initializer to block a return response
        '''
        DiagnosticStatusResponse.__init__(self, **kwargs)
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
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
# Diagnostic Sub Code 19
#---------------------------------------------------------------------------#
class ReturnIopOverrunCountRequest(DiagnosticStatusSimpleRequest):
    '''
    An IOP overrun is caused by data characters arriving at the port
    faster than they can be stored, or by the loss of a character due
    to a hardware malfunction.  This function is specific to the 884.
    '''
    sub_function_code = 0x0013

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
        '''
        count = _MCB.Counter.BusCharacterOverrun
        return ReturnIopOverrunCountResponse(count)


class ReturnIopOverrunCountResponse(DiagnosticStatusSimpleResponse):
    '''
    The response data field returns the quantity of messages
    addressed to the slave that it could not handle due to an 884
    IOP overrun condition, since its last restart, clear counters
    operation, or power-up.
    '''
    sub_function_code = 0x0013


#---------------------------------------------------------------------------#
# Diagnostic Sub Code 20
#---------------------------------------------------------------------------#
class ClearOverrunCountRequest(DiagnosticStatusSimpleRequest):
    '''
    Clears the overrun error counter and reset the error flag

    An error flag should be cleared, but nothing else in the
    specification mentions is, so it is ignored.
    '''
    sub_function_code = 0x0014

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
        '''
        _MCB.Counter.BusCharacterOverrun = 0x0000
        return ClearOverrunCountResponse(self.message)


class ClearOverrunCountResponse(DiagnosticStatusSimpleResponse):
    '''
    Clears the overrun error counter and reset the error flag
    '''
    sub_function_code = 0x0014


#---------------------------------------------------------------------------#
# Diagnostic Sub Code 21
#---------------------------------------------------------------------------#
class GetClearModbusPlusRequest(DiagnosticStatusSimpleRequest):
    '''
    In addition to the Function code (08) and Subfunction code
    (00 15 hex) in the query, a two-byte Operation field is used
    to specify either a 'Get Statistics' or a 'Clear Statistics'
    operation.  The two operations are exclusive - the 'Get'
    operation cannot clear the statistics, and the 'Clear'
    operation does not return statistics prior to clearing
    them. Statistics are also cleared on power-up of the slave
    device.
    '''
    sub_function_code = 0x0015

    def __init__(self, **kwargs):
        super(GetClearModbusPlusRequest, self).__init__(**kwargs)

    def get_response_pdu_size(self):
        """
        Returns a series of 54 16-bit words (108 bytes) in the data field of the response
        (this function differs from the usual two-byte length of the data field). The data
        contains the statistics for the Modbus Plus peer processor in the slave device.
        Func_code (1 byte) + Sub function code (2 byte) + Operation (2 byte) + Data (108 bytes)
        :return:
        """
        if self.message == ModbusPlusOperation.GetStatistics:
            data = 2 + 108 # byte count(2) + data (54*2)
        else:
            data = 0
        return 1 + 2 + 2 + 2+ data

    def execute(self, *args):
        ''' Execute the diagnostic request on the given device

        :returns: The initialized response message
        '''
        message = None # the clear operation does not return info
        if self.message == ModbusPlusOperation.ClearStatistics:
            _MCB.Plus.reset()
            message = self.message
        else:
            message = [self.message]
            message += _MCB.Plus.encode()
        return GetClearModbusPlusResponse(message)

    def encode(self):
        '''
        Base encoder for a diagnostic response
        we encode the data set in self.message

        :returns: The encoded packet
        '''
        packet = struct.pack('>H', self.sub_function_code)
        packet += struct.pack('>H', self.message)
        return packet


class GetClearModbusPlusResponse(DiagnosticStatusSimpleResponse):
    '''
    Returns a series of 54 16-bit words (108 bytes) in the data field
    of the response (this function differs from the usual two-byte
    length of the data field). The data contains the statistics for
    the Modbus Plus peer processor in the slave device.
    '''
    sub_function_code = 0x0015


#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "DiagnosticStatusRequest", "DiagnosticStatusResponse",
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
    "ReturnIopOverrunCountRequest", "ReturnIopOverrunCountResponse",
    "ClearOverrunCountRequest", "ClearOverrunCountResponse",
    "GetClearModbusPlusRequest", "GetClearModbusPlusResponse",
]
