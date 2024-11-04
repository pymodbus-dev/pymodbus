"""Diagnostic Record Read/Write."""
from __future__ import annotations

import struct

from pymodbus.constants import ModbusPlusOperation, ModbusStatus
from pymodbus.device import ModbusControlBlock
from pymodbus.exceptions import ModbusException
from pymodbus.pdu.pdu import ModbusPDU
from pymodbus.utilities import pack_bitstring


_MCB = ModbusControlBlock()


class DiagnosticStatusRequest(ModbusPDU):
    """DiagnosticStatusRequest."""

    function_code = 0x08
    sub_function_code: int = 9999
    rtu_frame_size = 8

    def __init__(self, slave_id=1, transaction_id=0) -> None:
        """Initialize a diagnostic request."""
        super().__init__(transaction_id=transaction_id, slave_id=slave_id)
        self.message: bytes | int | list | tuple | None = None


    def encode(self):
        """Encode a diagnostic response."""
        packet = struct.pack(">H", self.sub_function_code)
        if self.message is not None:
            if isinstance(self.message, bytes):
                packet += self.message
                return packet
            if isinstance(self.message, int):
                packet += struct.pack(">H", self.message)
                return packet

            if isinstance(self.message, (list, tuple)):
                if len(self.message) > 1:
                    raise RuntimeError("!!! self.message multiple entries !!!")

                for piece in self.message:
                    packet += struct.pack(">H", piece)
                return packet
            raise RuntimeError(f"UNKNOWN DIAG message type: {type(self.message)}")
        return packet

    def decode(self, data):
        """Decode a diagnostic request."""
        (self.sub_function_code, ) = struct.unpack(">H", data[:2])
        if self.sub_function_code == ReturnQueryDataRequest.sub_function_code:
            self.message = data[2:]
        elif len(data) > 2:
            (self.message,) = struct.unpack(">H", data[2:])

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Sub function code (2 byte) + Data (2 * N bytes)
        """
        return 1 + 2 + 2

    async def update_datastore(self, *args):
        """Implement dummy."""
        return DiagnosticStatusResponse(args)


class DiagnosticStatusResponse(ModbusPDU):
    """Diagnostic status.

    This is a base class for all of the diagnostic response functions

    It works by performing all of the encoding and decoding of variable
    data and lets the higher classes define what extra data to append
    and how to update_datastore a request
    """

    function_code = 0x08
    sub_function_code = 9999
    rtu_frame_size = 8

    def __init__(self, slave_id=1, transaction_id=0):
        """Initialize a diagnostic response."""
        super().__init__(transaction_id=transaction_id, slave_id=slave_id)
        self.message = None

    def encode(self):
        """Encode diagnostic response."""
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
        """Decode diagnostic response."""
        (self.sub_function_code, ) = struct.unpack(">H", data[:2])
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


class ReturnQueryDataRequest(DiagnosticStatusRequest):
    """Return query data.

    The data passed in the request data field is to be returned (looped back)
    in the response. The entire response message should be identical to the
    request.
    """

    sub_function_code = 0x0000

    def __init__(self, message=b"\x00\x00", slave_id=1, transaction_id=0):
        """Initialize a new instance of the request.

        :param message: The message to send to loopback
        """
        DiagnosticStatusRequest.__init__(self, slave_id=slave_id, transaction_id=transaction_id)
        if not isinstance(message, bytes):
            raise ModbusException(f"message({type(message)}) must be bytes")
        self.message = message

    async def update_datastore(self, *_args):
        """update_datastore the loopback request (builds the response).

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

    def __init__(self, message=b"\x00\x00", slave_id=1, transaction_id=0):
        """Initialize a new instance of the response.

        :param message: The message to loopback
        """
        DiagnosticStatusResponse.__init__(self, slave_id=slave_id, transaction_id=transaction_id)
        if not isinstance(message, bytes):
            raise ModbusException(f"message({type(message)}) must be bytes")
        self.message = message


class RestartCommunicationsOptionRequest(DiagnosticStatusRequest):
    """Restart communication.

    The remote device serial line port must be initialized and restarted, and
    all of its communications event counters are cleared. If the port is
    currently in Listen Only Mode, no response is returned. This function is
    the only one that brings the port out of Listen Only Mode. If the port is
    not currently in Listen Only Mode, a normal response is returned. This
    occurs before the restart is update_datastored.
    """

    sub_function_code = 0x0001

    def __init__(self, toggle=False, slave_id=1, transaction_id=0):
        """Initialize a new request.

        :param toggle: Set to True to toggle, False otherwise
        """
        DiagnosticStatusRequest.__init__(self, slave_id=slave_id, transaction_id=transaction_id)
        if toggle:
            self.message = [ModbusStatus.ON]
        else:
            self.message = [ModbusStatus.OFF]

    async def update_datastore(self, *_args):
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
    occurs before the restart is update_datastored.
    """

    sub_function_code = 0x0001

    def __init__(self, toggle=False, slave_id=1, transaction_id=0):
        """Initialize a new response.

        :param toggle: Set to True if we toggled, False otherwise
        """
        DiagnosticStatusResponse.__init__(self, slave_id=slave_id, transaction_id=transaction_id)
        if toggle:
            self.message = [ModbusStatus.ON]
        else:
            self.message = [ModbusStatus.OFF]


class DiagnosticStatusSimpleRequest(DiagnosticStatusRequest):
    """Return diagnostic status.

    A large majority of the diagnostic functions are simple
    status request functions.  They work by sending 0x0000
    as data and their function code and they are returned
    2 bytes of data.

    If a function inherits this, they only need to implement
    the update_datastore method
    """

    def __init__(self, data=0x0000, slave_id=1, transaction_id=0):
        """Initialize a simple diagnostic request.

        The data defaults to 0x0000 if not provided as over half
        of the functions require it.

        :param data: The data to send along with the request
        """
        DiagnosticStatusRequest.__init__(self, slave_id=slave_id, transaction_id=transaction_id)
        self.message = data


class DiagnosticStatusSimpleResponse(DiagnosticStatusResponse):
    """Diagnostic status.

    A large majority of the diagnostic functions are simple
    status request functions.  They work by sending 0x0000
    as data and their function code and they are returned
    2 bytes of data.
    """

    def __init__(self, data=0x0000, slave_id=1, transaction_id=0):
        """Return a simple diagnostic response.

        :param data: The resulting data to return to the client
        """
        DiagnosticStatusResponse.__init__(self, slave_id=slave_id, transaction_id=transaction_id)
        self.message = data


class ReturnDiagnosticRegisterRequest(DiagnosticStatusSimpleRequest):
    """The contents of the remote device's 16-bit diagnostic register are returned in the response."""

    sub_function_code = 0x0002

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

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


class ChangeAsciiInputDelimiterRequest(DiagnosticStatusSimpleRequest):
    """Change ascii input delimiter.

    The character "CHAR" passed in the request data field becomes the end of
    message delimiter for future messages (replacing the default LF
    character). This function is useful in cases of a Line Feed is not
    required at the end of ASCII messages.
    """

    sub_function_code = 0x0003

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        char = (self.message & 0xFF00) >> 8  # type: ignore[operator]
        _MCB.Delimiter = char
        return ChangeAsciiInputDelimiterResponse(self.message)


class ChangeAsciiInputDelimiterResponse(DiagnosticStatusSimpleResponse):
    """Change ascii input delimiter.

    The character "CHAR" passed in the request data field becomes the end of
    message delimiter for future messages (replacing the default LF
    character). This function is useful in cases of a Line Feed is not
    required at the end of ASCII messages.
    """

    sub_function_code = 0x0003


class ForceListenOnlyModeRequest(DiagnosticStatusSimpleRequest):
    """Forces the addressed remote device to its Listen Only Mode for MODBUS communications.

    This isolates it from the other devices on the network,
    allowing them to continue communicating without interruption from the
    addressed remote device. No response is returned.
    """

    sub_function_code = 0x0004

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        _MCB.ListenOnly = True
        return ForceListenOnlyModeResponse()


class ForceListenOnlyModeResponse(DiagnosticStatusResponse):
    """Forces the addressed remote device to its Listen Only Mode for MODBUS communications.

    This isolates it from the other devices on the network,
    allowing them to continue communicating without interruption from the
    addressed remote device. No response is returned.

    This does not send a response
    """

    sub_function_code = 0x0004

    def __init__(self, slave_id=1, transaction_id=0):
        """Initialize to block a return response."""
        DiagnosticStatusResponse.__init__(self, slave_id=slave_id, transaction_id=transaction_id)
        self.message = []


class ClearCountersRequest(DiagnosticStatusSimpleRequest):
    """Clear ll counters and the diagnostic register.

    Also, counters are cleared upon power-up
    """

    sub_function_code = 0x000A

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        _MCB.reset()
        return ClearCountersResponse(self.message)


class ClearCountersResponse(DiagnosticStatusSimpleResponse):
    """Clear ll counters and the diagnostic register.

    Also, counters are cleared upon power-up
    """

    sub_function_code = 0x000A


class ReturnBusMessageCountRequest(DiagnosticStatusSimpleRequest):
    """Return bus message count.

    The response data field returns the quantity of messages that the
    remote device has detected on the communications systems since its last
    restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000B

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

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


class ReturnBusCommunicationErrorCountRequest(DiagnosticStatusSimpleRequest):
    """Return bus comm. count.

    The response data field returns the quantity of CRC errors encountered
    by the remote device since its last restart, clear counter operation, or
    power-up
    """

    sub_function_code = 0x000C

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

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


class ReturnBusExceptionErrorCountRequest(DiagnosticStatusSimpleRequest):
    """Return bus exception.

    The response data field returns the quantity of modbus exception
    responses returned by the remote device since its last restart,
    clear counters operation, or power-up
    """

    sub_function_code = 0x000D

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

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


class ReturnSlaveMessageCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave message count.

    The response data field returns the quantity of messages addressed to the
    remote device, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000E

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveMessage
        return ReturnSlaveMessageCountResponse(count)


class ReturnSlaveMessageCountResponse(DiagnosticStatusSimpleResponse):
    """Return slave message count.

    The response data field returns the quantity of messages addressed to the
    remote device, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000E


class ReturnSlaveNoResponseCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave no response.

    The response data field returns the quantity of messages addressed to the
    remote device, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000F

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveNoResponse
        return ReturnSlaveNoResponseCountResponse(count)


class ReturnSlaveNoResponseCountResponse(DiagnosticStatusSimpleResponse):
    """Return slave no response.

    The response data field returns the quantity of messages addressed to the
    remote device, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000F


class ReturnSlaveNAKCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave NAK count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Negative ACKNOWLEDGE (NAK) exception
    response, since its last restart, clear counters operation, or power-up.
    Exception responses are described and listed in section 7 .
    """

    sub_function_code = 0x0010

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveNAK
        return ReturnSlaveNAKCountResponse(count)


class ReturnSlaveNAKCountResponse(DiagnosticStatusSimpleResponse):
    """Return slave NAK.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Negative ACKNOWLEDGE (NAK) exception
    response, since its last restart, clear counters operation, or power-up.
    Exception responses are described and listed in section 7.
    """

    sub_function_code = 0x0010


class ReturnSlaveBusyCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave busy count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Slave Device Busy exception response,
    since its last restart, clear counters operation, or power-up.
    """

    sub_function_code = 0x0011

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SLAVE_BUSY
        return ReturnSlaveBusyCountResponse(count)


class ReturnSlaveBusyCountResponse(DiagnosticStatusSimpleResponse):
    """Return slave busy count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Slave Device Busy exception response,
    since its last restart, clear counters operation, or power-up.
    """

    sub_function_code = 0x0011


class ReturnSlaveBusCharacterOverrunCountRequest(DiagnosticStatusSimpleRequest):
    """Return slave character overrun.

    The response data field returns the quantity of messages addressed to the
    remote device that it could not handle due to a character overrun condition,
    since its last restart, clear counters operation, or power-up. A character
    overrun is caused by data characters arriving at the port faster than they
    can be stored, or by the loss of a character due to a hardware malfunction.
    """

    sub_function_code = 0x0012

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

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


class ReturnIopOverrunCountRequest(DiagnosticStatusSimpleRequest):
    """Return IopOverrun.

    An IOP overrun is caused by data characters arriving at the port
    faster than they can be stored, or by the loss of a character due
    to a hardware malfunction.  This function is specific to the 884.
    """

    sub_function_code = 0x0013

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

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


class ClearOverrunCountRequest(DiagnosticStatusSimpleRequest):
    """Clear the overrun error counter and reset the error flag.

    An error flag should be cleared, but nothing else in the
    specification mentions is, so it is ignored.
    """

    sub_function_code = 0x0014

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        _MCB.Counter.BusCharacterOverrun = 0x0000
        return ClearOverrunCountResponse(self.message)


class ClearOverrunCountResponse(DiagnosticStatusSimpleResponse):
    """Clear the overrun error counter and reset the error flag."""

    sub_function_code = 0x0014


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

    def __init__(self, data=0, slave_id=1, transaction_id=0):
        """Initialize."""
        super().__init__(slave_id=slave_id, transaction_id=transaction_id)
        self.message=data

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

    async def update_datastore(self, *args):
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        message: int | list | None = None  # the clear operation does not return info
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
