"""Diagnostic Record Read/Write.

These need to be tied into a the current server context
or linked to the appropriate data
"""

__all__ = [
    "DiagnosticStatusRequest",
    "DiagnosticStatusResponse",
    "ReturnQueryDataRequest",
    "ReturnQueryDataResponse",
    "RestartCommunicationsOptionRequest",
    "RestartCommunicationsOptionResponse",
    "ReturnDiagnosticRegisterRequest",
    "ReturnDiagnosticRegisterResponse",
    "ChangeAsciiInputDelimiterRequest",
    "ChangeAsciiInputDelimiterResponse",
    "ForceListenOnlyModeRequest",
    "ForceListenOnlyModeResponse",
    "ClearCountersRequest",
    "ClearCountersResponse",
    "ReturnBusMessageCountRequest",
    "ReturnBusMessageCountResponse",
    "ReturnBusCommunicationErrorCountRequest",
    "ReturnBusCommunicationErrorCountResponse",
    "ReturnBusExceptionErrorCountRequest",
    "ReturnBusExceptionErrorCountResponse",
    "ReturnSlaveMessageCountRequest",
    "ReturnSlaveMessageCountResponse",
    "ReturnSlaveNoResponseCountRequest",
    "ReturnSlaveNoResponseCountResponse",
    "ReturnSlaveNAKCountRequest",
    "ReturnSlaveNAKCountResponse",
    "ReturnSlaveBusyCountRequest",
    "ReturnSlaveBusyCountResponse",
    "ReturnSlaveBusCharacterOverrunCountRequest",
    "ReturnSlaveBusCharacterOverrunCountResponse",
    "ReturnIopOverrunCountRequest",
    "ReturnIopOverrunCountResponse",
    "ClearOverrunCountRequest",
    "ClearOverrunCountResponse",
    "GetClearModbusPlusRequest",
    "GetClearModbusPlusResponse",
]

# pylint: disable=missing-type-doc
import struct

from pymodbus.constants import ModbusPlusOperation, ModbusStatus
from pymodbus.device import ModbusControlBlock
from pymodbus.exceptions import ModbusException, NotImplementedException
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.utilities import pack_bitstring


_MCB = ModbusControlBlock()


# ---------------------------------------------------------------------------#
#  Diagnostic Function Codes Base Classes
#  diagnostic 08, 00-18,20
# ---------------------------------------------------------------------------#
#  TODO Make sure all the data is decoded from the response # pylint: disable=fixme
# ---------------------------------------------------------------------------#
class DiagnosticStatusRequest(ModbusRequest):
    """This is a base class for all of the diagnostic request functions."""

    function_code = 0x08
    function_code_name = "diagnostic_status"
    _rtu_frame_size = 8

    def __init__(self, **kwargs):
        """Initialize a diagnostic request."""
        ModbusRequest.__init__(self, **kwargs)
        self.message = None

    def encode(self):
        """Encode a diagnostic response.

        we encode the data set in self.message

        :returns: The encoded packet
        """
        packet = struct.pack(">H", self.sub_function_code)
        if self.message is not None:
            if isinstance(self.message, str):
                packet += self.message.encode()
            elif isinstance(self.message, bytes):
                packet += self.message
            elif isinstance(self.message, (list, tuple)):
                for piece in self.message:
                    packet += struct.pack(">H", piece)
            elif isinstance(self.message, int):
                packet += struct.pack(">H", self.message)
        return packet

    def decode(self, data):
        """Decode a diagnostic request.

        :param data: The data to decode into the function code
        """
        (
            self.sub_function_code,  # pylint: disable=attribute-defined-outside-init
        ) = struct.unpack(">H", data[:2])
        if self.sub_function_code == ReturnQueryDataRequest.sub_function_code:
            self.message = data[2:]
        else:
            (self.message,) = struct.unpack(">H", data[2:])

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Sub function code (2 byte) + Data (2 * N bytes)
        :return:
        """
        if not isinstance(self.message, list):
            self.message = [self.message]
        return 1 + 2 + 2 * len(self.message)


class DiagnosticStatusResponse(ModbusResponse):
    """Diagnostic status.

    This is a base class for all of the diagnostic response functions

    It works by performing all of the encoding and decoding of variable
    data and lets the higher classes define what extra data to append
    and how to execute a request
    """

    function_code = 0x08
    _rtu_frame_size = 8

    def __init__(self, **kwargs):
        """Initialize a diagnostic response."""
        ModbusResponse.__init__(self, **kwargs)
        self.message = None

    def encode(self):
        """Encode diagnostic response.

        we encode the data set in self.message

        :returns: The encoded packet
        """
        packet = struct.pack(">H", self.sub_function_code)
        if self.message is not None:
            if isinstance(self.message, str):
                packet += self.message.encode()
            elif isinstance(self.message, bytes):
                packet += self.message
            elif isinstance(self.message, (list, tuple)):
                for piece in self.message:
                    packet += struct.pack(">H", piece)
            elif isinstance(self.message, int):
                packet += struct.pack(">H", self.message)
        return packet

    def decode(self, data):
        """Decode diagnostic response.

        :param data: The data to decode into the function code
        """
        (
            self.sub_function_code,  # pylint: disable=attribute-defined-outside-init
        ) = struct.unpack(">H", data[:2])
        data = data[2:]
        if self.sub_function_code == ReturnQueryDataRequest.sub_function_code:
            self.message = data
        else:
            word_len = len(data) // 2
            if len(data) % 2:
                word_len += 1
                data += b"0"
            data = struct.unpack(">" + "H" * word_len, data)
            self.message = data


class DiagnosticStatusSimpleRequest(DiagnosticStatusRequest):
    """Return diagnostic status.

    A large majority of the diagnostic functions are simple
    status request functions.  They work by sending 0x0000
    as data and their function code and they are returned
    2 bytes of data.

    If a function inherits this, they only need to implement
    the execute method
    """

    def __init__(self, data=0x0000, **kwargs):
        """Initialize a simple diagnostic request.

        The data defaults to 0x0000 if not provided as over half
        of the functions require it.

        :param data: The data to send along with the request
        """
        DiagnosticStatusRequest.__init__(self, **kwargs)
        self.message = data

    def execute(self, *args):
        """Raise if not implemented."""
        raise NotImplementedException("Diagnostic Message Has No Execute Method")


class DiagnosticStatusSimpleResponse(DiagnosticStatusResponse):
    """Diagnostic status.

    A large majority of the diagnostic functions are simple
    status request functions.  They work by sending 0x0000
    as data and their function code and they are returned
    2 bytes of data.
    """

    def __init__(self, data=0x0000, **kwargs):
        """Return a simple diagnostic response.

        :param data: The resulting data to return to the client
        """
        DiagnosticStatusResponse.__init__(self, **kwargs)
        self.message = data


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 00
# ---------------------------------------------------------------------------#
class ReturnQueryDataRequest(DiagnosticStatusRequest):
    """Return query data.

    The data passed in the request data field is to be returned (looped back)
    in the response. The entire response message should be identical to the
    request.
    """

    sub_function_code = 0x0000

    def __init__(self, message=b"\x00\x00", slave=None, **kwargs):
        """Initialize a new instance of the request.

        :param message: The message to send to loopback
        """
        DiagnosticStatusRequest.__init__(self, slave=slave, **kwargs)
        if not isinstance(message, bytes):
            raise ModbusException(f"message({type(message)}) must be bytes")
        self.message = message

    def execute(self, *_args):
        """Execute the loopback request (builds the response).

        :returns: The populated loopback response message
        """
        return ReturnQueryDataResponse(self.message)


class ReturnQueryDataResponse(DiagnosticStatusResponse):
    """Return query data.

    The data passed in the request data field is to be returned (looped back)
    in the response. The entire response message should be identical to the
    request.
    """

    sub_function_code = 0x0000

    def __init__(self, message=b"\x00\x00", **kwargs):
        """Initialize a new instance of the response.

        :param message: The message to loopback
        """
        DiagnosticStatusResponse.__init__(self, **kwargs)
        if not isinstance(message, bytes):
            raise ModbusException(f"message({type(message)}) must be bytes")
        self.message = message


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 01
# ---------------------------------------------------------------------------#
class RestartCommunicationsOptionRequest(DiagnosticStatusRequest):
    """Restart communication.

    The remote device serial line port must be initialized and restarted, and
    all of its communications event counters are cleared. If the port is
    currently in Listen Only Mode, no response is returned. This function is
    the only one that brings the port out of Listen Only Mode. If the port is
    not currently in Listen Only Mode, a normal response is returned. This
    occurs before the restart is executed.
    """

    sub_function_code = 0x0001

    def __init__(self, toggle=False, slave=None, **kwargs):
        """Initialize a new request.

        :param toggle: Set to True to toggle, False otherwise
        """
        DiagnosticStatusRequest.__init__(self, slave=slave, **kwargs)
        if toggle:
            self.message = [ModbusStatus.ON]
        else:
            self.message = [ModbusStatus.OFF]

    def execute(self, *_args):
        """Clear event log and restart.

        :returns: The initialized response message
        """
        # if _MCB.ListenOnly:
        return RestartCommunicationsOptionResponse(self.message)


class RestartCommunicationsOptionResponse(DiagnosticStatusResponse):
    """Restart Communication.

    The remote device serial line port must be initialized and restarted, and
    all of its communications event counters are cleared. If the port is
    currently in Listen Only Mode, no response is returned. This function is
    the only one that brings the port out of Listen Only Mode. If the port is
    not currently in Listen Only Mode, a normal response is returned. This
    occurs before the restart is executed.
    """

    sub_function_code = 0x0001

    def __init__(self, toggle=False, **kwargs):
        """Initialize a new response.

        :param toggle: Set to True if we toggled, False otherwise
        """
        DiagnosticStatusResponse.__init__(self, **kwargs)
        if toggle:
            self.message = [ModbusStatus.ON]
        else:
            self.message = [ModbusStatus.OFF]


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 02
# ---------------------------------------------------------------------------#
class ReturnDiagnosticRegisterRequest(DiagnosticStatusSimpleRequest):
    """The contents of the remote device's 16-bit diagnostic register are returned in the response."""

    sub_function_code = 0x0002

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        # if _MCB.isListenOnly():
        register = pack_bitstring(_MCB.getDiagnosticRegister())
        return ReturnDiagnosticRegisterResponse(register)


class ReturnDiagnosticRegisterResponse(DiagnosticStatusSimpleResponse):
    """Return diagnostic register.

    The contents of the remote device's 16-bit diagnostic register are
    returned in the response
    """

    sub_function_code = 0x0002


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 03
# ---------------------------------------------------------------------------#
class ChangeAsciiInputDelimiterRequest(DiagnosticStatusSimpleRequest):
    """Change ascii input delimiter.

    The character "CHAR" passed in the request data field becomes the end of
    message delimiter for future messages (replacing the default LF
    character). This function is useful in cases of a Line Feed is not
    required at the end of ASCII messages.
    """

    sub_function_code = 0x0003

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        char = (self.message & 0xFF00) >> 8  # type: ignore[operator]
        _MCB._setDelimiter(char)  # pylint: disable=protected-access
        return ChangeAsciiInputDelimiterResponse(self.message)


class ChangeAsciiInputDelimiterResponse(DiagnosticStatusSimpleResponse):
    """Change ascii input delimiter.

    The character "CHAR" passed in the request data field becomes the end of
    message delimiter for future messages (replacing the default LF
    character). This function is useful in cases of a Line Feed is not
    required at the end of ASCII messages.
    """

    sub_function_code = 0x0003


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 04
# ---------------------------------------------------------------------------#
class ForceListenOnlyModeRequest(DiagnosticStatusSimpleRequest):
    """Forces the addressed remote device to its Listen Only Mode for MODBUS communications.

    This isolates it from the other devices on the network,
    allowing them to continue communicating without interruption from the
    addressed remote device. No response is returned.
    """

    sub_function_code = 0x0004

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        _MCB._setListenOnly(True)  # pylint: disable=protected-access
        return ForceListenOnlyModeResponse()


class ForceListenOnlyModeResponse(DiagnosticStatusResponse):
    """Forces the addressed remote device to its Listen Only Mode for MODBUS communications.

    This isolates it from the other devices on the network,
    allowing them to continue communicating without interruption from the
    addressed remote device. No response is returned.

    This does not send a response
    """

    sub_function_code = 0x0004
    should_respond = False

    def __init__(self, **kwargs):
        """Initialize to block a return response."""
        DiagnosticStatusResponse.__init__(self, **kwargs)
        self.message = []


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 10
# ---------------------------------------------------------------------------#
class ClearCountersRequest(DiagnosticStatusSimpleRequest):
    """Clear ll counters and the diagnostic register.

    Also, counters are cleared upon power-up
    """

    sub_function_code = 0x000A

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        _MCB.reset()
        return ClearCountersResponse(self.message)


class ClearCountersResponse(DiagnosticStatusSimpleResponse):
    """Clear ll counters and the diagnostic register.

    Also, counters are cleared upon power-up
    """

    sub_function_code = 0x000A


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 11
# ---------------------------------------------------------------------------#
class ReturnBusMessageCountRequest(DiagnosticStatusSimpleRequest):
    """Return bus message count.

    The response data field returns the quantity of messages that the
    remote device has detected on the communications systems since its last
    restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000B

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusMessage
        return ReturnBusMessageCountResponse(count)


class ReturnBusMessageCountResponse(DiagnosticStatusSimpleResponse):
    """Return bus message count.

    The response data field returns the quantity of messages that the
    remote device has detected on the communications systems since its last
    restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000B


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 12
# ---------------------------------------------------------------------------#
class ReturnBusCommunicationErrorCountRequest(DiagnosticStatusSimpleRequest):
    """Return bus comm. count.

    The response data field returns the quantity of CRC errors encountered
    by the remote device since its last restart, clear counter operation, or
    power-up
    """

    sub_function_code = 0x000C

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusCommunicationError
        return ReturnBusCommunicationErrorCountResponse(count)


class ReturnBusCommunicationErrorCountResponse(DiagnosticStatusSimpleResponse):
    """Return bus comm. error.

    The response data field returns the quantity of CRC errors encountered
    by the remote device since its last restart, clear counter operation, or
    power-up
    """

    sub_function_code = 0x000C


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 13
# ---------------------------------------------------------------------------#
class ReturnBusExceptionErrorCountRequest(DiagnosticStatusSimpleRequest):
    """Return bus exception.

    The response data field returns the quantity of modbus exception
    responses returned by the remote device since its last restart,
    clear counters operation, or power-up
    """

    sub_function_code = 0x000D

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusExceptionError
        return ReturnBusExceptionErrorCountResponse(count)


class ReturnBusExceptionErrorCountResponse(DiagnosticStatusSimpleResponse):
    """Return bus exception.

    The response data field returns the quantity of modbus exception
    responses returned by the remote device since its last restart,
    clear counters operation, or power-up
    """

    sub_function_code = 0x000D


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 14
# ---------------------------------------------------------------------------#
class ReturnSlaveMessageCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave message count.

    The response data field returns the quantity of messages addressed to the
    remote device, or broadcast, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000E

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveMessage
        return ReturnSlaveMessageCountResponse(count)


class ReturnSlaveMessageCountResponse(DiagnosticStatusSimpleResponse):
    """Return slave message count.

    The response data field returns the quantity of messages addressed to the
    remote device, or broadcast, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000E


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 15
# ---------------------------------------------------------------------------#
class ReturnSlaveNoResponseCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave no response.

    The response data field returns the quantity of messages addressed to the
    remote device, or broadcast, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000F

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveNoResponse
        return ReturnSlaveNoResponseCountResponse(count)


class ReturnSlaveNoResponseCountResponse(DiagnosticStatusSimpleResponse):
    """Return slave no response.

    The response data field returns the quantity of messages addressed to the
    remote device, or broadcast, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000F


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 16
# ---------------------------------------------------------------------------#
class ReturnSlaveNAKCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave NAK count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Negative Acknowledge (NAK) exception
    response, since its last restart, clear counters operation, or power-up.
    Exception responses are described and listed in section 7 .
    """

    sub_function_code = 0x0010

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveNAK
        return ReturnSlaveNAKCountResponse(count)


class ReturnSlaveNAKCountResponse(DiagnosticStatusSimpleResponse):
    """Return slave NAK.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Negative Acknowledge (NAK) exception
    response, since its last restart, clear counters operation, or power-up.
    Exception responses are described and listed in section 7.
    """

    sub_function_code = 0x0010


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 17
# ---------------------------------------------------------------------------#
class ReturnSlaveBusyCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave busy count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Slave Device Busy exception response,
    since its last restart, clear counters operation, or power-up.
    """

    sub_function_code = 0x0011

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveBusy
        return ReturnSlaveBusyCountResponse(count)


class ReturnSlaveBusyCountResponse(DiagnosticStatusSimpleResponse):
    """Return slave busy count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Slave Device Busy exception response,
    since its last restart, clear counters operation, or power-up.
    """

    sub_function_code = 0x0011


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 18
# ---------------------------------------------------------------------------#
class ReturnSlaveBusCharacterOverrunCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave character overrun.

    The response data field returns the quantity of messages addressed to the
    remote device that it could not handle due to a character overrun condition,
    since its last restart, clear counters operation, or power-up. A character
    overrun is caused by data characters arriving at the port faster than they
    can be stored, or by the loss of a character due to a hardware malfunction.
    """

    sub_function_code = 0x0012

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusCharacterOverrun
        return ReturnSlaveBusCharacterOverrunCountResponse(count)


class ReturnSlaveBusCharacterOverrunCountResponse(DiagnosticStatusSimpleResponse):
    """Return the quantity of messages addressed to the remote device unhandled due to a character overrun.

    Since its last restart, clear counters operation, or power-up. A character
    overrun is caused by data characters arriving at the port faster than they
    can be stored, or by the loss of a character due to a hardware malfunction.
    """

    sub_function_code = 0x0012


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 19
# ---------------------------------------------------------------------------#
class ReturnIopOverrunCountRequest(DiagnosticStatusSimpleRequest):
    """Return IopOverrun.

    An IOP overrun is caused by data characters arriving at the port
    faster than they can be stored, or by the loss of a character due
    to a hardware malfunction.  This function is specific to the 884.
    """

    sub_function_code = 0x0013

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusCharacterOverrun
        return ReturnIopOverrunCountResponse(count)


class ReturnIopOverrunCountResponse(DiagnosticStatusSimpleResponse):
    """Return Iop overrun count.

    The response data field returns the quantity of messages
    addressed to the slave that it could not handle due to an 884
    IOP overrun condition, since its last restart, clear counters
    operation, or power-up.
    """

    sub_function_code = 0x0013


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 20
# ---------------------------------------------------------------------------#
class ClearOverrunCountRequest(DiagnosticStatusSimpleRequest):
    """Clear the overrun error counter and reset the error flag.

    An error flag should be cleared, but nothing else in the
    specification mentions is, so it is ignored.
    """

    sub_function_code = 0x0014

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        _MCB.Counter.BusCharacterOverrun = 0x0000
        return ClearOverrunCountResponse(self.message)


class ClearOverrunCountResponse(DiagnosticStatusSimpleResponse):
    """Clear the overrun error counter and reset the error flag."""

    sub_function_code = 0x0014


# ---------------------------------------------------------------------------#
#  Diagnostic Sub Code 21
# ---------------------------------------------------------------------------#
class GetClearModbusPlusRequest(DiagnosticStatusSimpleRequest):
    """Get/Clear modbus plus request.

    In addition to the Function code (08) and Subfunction code
    (00 15 hex) in the query, a two-byte Operation field is used
    to specify either a "Get Statistics" or a "Clear Statistics"
    operation.  The two operations are exclusive - the "Get"
    operation cannot clear the statistics, and the "Clear"
    operation does not return statistics prior to clearing
    them. Statistics are also cleared on power-up of the slave
    device.
    """

    sub_function_code = 0x0015

    def __init__(self, slave=None, **kwargs):
        """Initialize."""
        super().__init__(slave=slave, **kwargs)

    def get_response_pdu_size(self):
        """Return a series of 54 16-bit words (108 bytes) in the data field of the response.

        This function differs from the usual two-byte length of the data field.
        The data contains the statistics for the Modbus Plus peer processor in the slave device.
        Func_code (1 byte) + Sub function code (2 byte) + Operation (2 byte) + Data (108 bytes)
        :return:
        """
        if self.message == ModbusPlusOperation.GET_STATISTICS:
            data = 2 + 108  # byte count(2) + data (54*2)
        else:
            data = 0
        return 1 + 2 + 2 + 2 + data

    def execute(self, *args):
        """Execute the diagnostic request on the given device.

        :returns: The initialized response message
        """
        message = None  # the clear operation does not return info
        if self.message == ModbusPlusOperation.CLEAR_STATISTICS:
            _MCB.Plus.reset()
            message = self.message
        else:
            message = [self.message]
            message += _MCB.Plus.encode()
        return GetClearModbusPlusResponse(message)

    def encode(self):
        """Encode a diagnostic response.

        we encode the data set in self.message

        :returns: The encoded packet
        """
        packet = struct.pack(">H", self.sub_function_code)
        packet += struct.pack(">H", self.message)
        return packet


class GetClearModbusPlusResponse(DiagnosticStatusSimpleResponse):
    """Return a series of 54 16-bit words (108 bytes) in the data field of the response.

    This function differs from the usual two-byte length of the data field.
    The data contains the statistics for the Modbus Plus peer processor in the slave device.
    """

    sub_function_code = 0x0015
