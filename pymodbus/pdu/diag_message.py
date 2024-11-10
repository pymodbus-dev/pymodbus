"""Diagnostic Record Read/Write."""
from __future__ import annotations

import struct
from typing import cast

from pymodbus.constants import ModbusPlusOperation
from pymodbus.datastore import ModbusSlaveContext
from pymodbus.device import ModbusControlBlock
from pymodbus.pdu.pdu import ModbusPDU
from pymodbus.utilities import pack_bitstring


_MCB = ModbusControlBlock()


class DiagnosticBase(ModbusPDU):
    """DiagnosticBase."""

    function_code = 0x08
    sub_function_code: int = 9999
    rtu_frame_size = 8

    def __init__(self, message: bytes | int | str | list | tuple | None = 0, slave_id: int = 1, transaction_id: int = 0) -> None:
        """Initialize a diagnostic request."""
        super().__init__(transaction_id=transaction_id, slave_id=slave_id)
        self.message: bytes | int | str | list | tuple | None = message

    def encode(self) -> bytes:
        """Encode a diagnostic response."""
        packet = struct.pack(">H", self.sub_function_code)
        if self.message is not None:
            if isinstance(self.message, str):
                packet += self.message.encode()
                return packet
            if isinstance(self.message, bytes):
                packet += self.message
                return packet
            if isinstance(self.message, int):
                packet += struct.pack(">H", self.message)
                return packet
            if isinstance(self.message, (list, tuple)):
                for piece in self.message:
                    packet += struct.pack(">H", piece)
                return packet
            raise RuntimeError(f"UNKNOWN DIAG message type: {type(self.message)}")
        return packet

    def decode(self, data: bytes) -> None:
        """Decode a diagnostic request."""
        (self.sub_function_code, ) = struct.unpack(">H", data[:2])
        data = data[2:]
        if self.sub_function_code == ReturnQueryDataRequest.sub_function_code:
            self.message = data
        elif (data_len := len(data)):
            if data_len % 2:
                data_len += 1
                data += b"0"
            if (word_len := data_len // 2) == 1:
                (self.message,) = struct.unpack(">H", data)
            else:
                self.message = struct.unpack(">" + "H" * word_len, data)

    def get_response_pdu_size(self) -> int:
        """Get response pdu size.

        Func_code (1 byte) + Sub function code (2 byte) + Data (2 * N bytes)
        """
        return 1 + 2 + 2

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """Implement dummy."""
        response = {
            DiagnosticBase.sub_function_code: DiagnosticBase,
            ReturnQueryDataResponse.sub_function_code: ReturnQueryDataResponse,
            RestartCommunicationsOptionResponse.sub_function_code: RestartCommunicationsOptionResponse,
        }[self.sub_function_code]
        return response(message=self.message, slave_id=self.slave_id, transaction_id=self.transaction_id)


class ReturnQueryDataRequest(DiagnosticBase):
    """ReturnQueryDataRequest."""

    sub_function_code = 0x0000


class ReturnQueryDataResponse(DiagnosticBase):
    """ReturnQueryDataResponse."""

    sub_function_code = 0x0000


class RestartCommunicationsOptionRequest(DiagnosticBase):
    """RestartCommunicationsOptionRequest."""

    sub_function_code = 0x0001


class RestartCommunicationsOptionResponse(DiagnosticBase):
    """RestartCommunicationsOptionResponse."""

    sub_function_code = 0x0001


class ReturnDiagnosticRegisterRequest(DiagnosticBase):
    """ReturnDiagnosticRegisterRequest."""

    sub_function_code = 0x0002

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device."""
        register = pack_bitstring(_MCB.getDiagnosticRegister())
        return ReturnDiagnosticRegisterResponse(message=register, slave_id=self.slave_id, transaction_id=self.transaction_id)


class ReturnDiagnosticRegisterResponse(DiagnosticBase):
    """ReturnDiagnosticRegisterResponse."""

    sub_function_code = 0x0002


class ChangeAsciiInputDelimiterRequest(DiagnosticBase):
    """ChangeAsciiInputDelimiterRequest."""

    sub_function_code = 0x0003

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device."""
        char = (cast(int, self.message) & 0xFF00) >> 8
        _MCB.Delimiter = char
        return ChangeAsciiInputDelimiterResponse(message=self.message, slave_id=self.slave_id, transaction_id=self.transaction_id)


class ChangeAsciiInputDelimiterResponse(DiagnosticBase):
    """ChangeAsciiInputDelimiterResponse."""

    sub_function_code = 0x0003


class ForceListenOnlyModeRequest(DiagnosticBase):
    """ForceListenOnlyModeRequest."""

    sub_function_code = 0x0004

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device."""
        _MCB.ListenOnly = True
        return ForceListenOnlyModeResponse(slave_id=self.slave_id, transaction_id=self.transaction_id)


class ForceListenOnlyModeResponse(DiagnosticBase):
    """ForceListenOnlyModeResponse.

    This does not send a response
    """

    sub_function_code = 0x0004

    def __init__(self, slave_id=1, transaction_id=0):
        """Initialize to block a return response."""
        DiagnosticBase.__init__(self, slave_id=slave_id, transaction_id=transaction_id)
        self.message = []


class ClearCountersRequest(DiagnosticBase):
    """ClearCountersRequest."""

    sub_function_code = 0x000A

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device."""
        _MCB.reset()
        return ClearCountersResponse(slave_id=self.slave_id, transaction_id=self.transaction_id)


class ClearCountersResponse(DiagnosticBase):
    """ClearCountersResponse."""

    sub_function_code = 0x000A


class ReturnBusMessageCountRequest(DiagnosticBase):
    """ReturnBusMessageCountRequest."""

    sub_function_code = 0x000B

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device."""
        count = _MCB.Counter.BusMessage
        return ReturnBusMessageCountResponse(message=count)


class ReturnBusMessageCountResponse(DiagnosticBase):
    """ReturnBusMessageCountResponse."""

    sub_function_code = 0x000B


class ReturnBusCommunicationErrorCountRequest(DiagnosticBase):
    """Return bus comm. count.

    The response data field returns the quantity of CRC errors encountered
    by the remote device since its last restart, clear counter operation, or
    power-up
    """

    sub_function_code = 0x000C

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusCommunicationError
        return ReturnBusCommunicationErrorCountResponse(count)


class ReturnBusCommunicationErrorCountResponse(DiagnosticBase):
    """Return bus comm. error.

    The response data field returns the quantity of CRC errors encountered
    by the remote device since its last restart, clear counter operation, or
    power-up
    """

    sub_function_code = 0x000C


class ReturnBusExceptionErrorCountRequest(DiagnosticBase):
    """Return bus exception.

    The response data field returns the quantity of modbus exception
    responses returned by the remote device since its last restart,
    clear counters operation, or power-up
    """

    sub_function_code = 0x000D

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusExceptionError
        return ReturnBusExceptionErrorCountResponse(count)


class ReturnBusExceptionErrorCountResponse(DiagnosticBase):
    """Return bus exception.

    The response data field returns the quantity of modbus exception
    responses returned by the remote device since its last restart,
    clear counters operation, or power-up
    """

    sub_function_code = 0x000D


class ReturnSlaveMessageCountRequest(DiagnosticBase):
    """Return slave message count.

    The response data field returns the quantity of messages addressed to the
    remote device, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000E

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveMessage
        return ReturnSlaveMessageCountResponse(count)


class ReturnSlaveMessageCountResponse(DiagnosticBase):
    """Return slave message count.

    The response data field returns the quantity of messages addressed to the
    remote device, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000E


class ReturnSlaveNoResponseCountRequest(DiagnosticBase):
    """Return slave no response.

    The response data field returns the quantity of messages addressed to the
    remote device, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000F

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveNoResponse
        return ReturnSlaveNoResponseCountResponse(count)


class ReturnSlaveNoResponseCountResponse(DiagnosticBase):
    """Return slave no response.

    The response data field returns the quantity of messages addressed to the
    remote device, that the remote device has processed since
    its last restart, clear counters operation, or power-up
    """

    sub_function_code = 0x000F


class ReturnSlaveNAKCountRequest(DiagnosticBase):
    """Return slave NAK count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Negative ACKNOWLEDGE (NAK) exception
    response, since its last restart, clear counters operation, or power-up.
    Exception responses are described and listed in section 7 .
    """

    sub_function_code = 0x0010

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SlaveNAK
        return ReturnSlaveNAKCountResponse(count)


class ReturnSlaveNAKCountResponse(DiagnosticBase):
    """Return slave NAK.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Negative ACKNOWLEDGE (NAK) exception
    response, since its last restart, clear counters operation, or power-up.
    Exception responses are described and listed in section 7.
    """

    sub_function_code = 0x0010


class ReturnSlaveBusyCountRequest(DiagnosticBase):
    """Return slave busy count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Slave Device Busy exception response,
    since its last restart, clear counters operation, or power-up.
    """

    sub_function_code = 0x0011

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.SLAVE_BUSY
        return ReturnSlaveBusyCountResponse(count)


class ReturnSlaveBusyCountResponse(DiagnosticBase):
    """Return slave busy count.

    The response data field returns the quantity of messages addressed to the
    remote device for which it returned a Slave Device Busy exception response,
    since its last restart, clear counters operation, or power-up.
    """

    sub_function_code = 0x0011


class ReturnSlaveBusCharacterOverrunCountRequest(DiagnosticBase):
    """Return slave character overrun.

    The response data field returns the quantity of messages addressed to the
    remote device that it could not handle due to a character overrun condition,
    since its last restart, clear counters operation, or power-up. A character
    overrun is caused by data characters arriving at the port faster than they
    can be stored, or by the loss of a character due to a hardware malfunction.
    """

    sub_function_code = 0x0012

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusCharacterOverrun
        return ReturnSlaveBusCharacterOverrunCountResponse(count)


class ReturnSlaveBusCharacterOverrunCountResponse(DiagnosticBase):
    """Return the quantity of messages addressed to the remote device unhandled due to a character overrun.

    Since its last restart, clear counters operation, or power-up. A character
    overrun is caused by data characters arriving at the port faster than they
    can be stored, or by the loss of a character due to a hardware malfunction.
    """

    sub_function_code = 0x0012


class ReturnIopOverrunCountRequest(DiagnosticBase):
    """Return IopOverrun.

    An IOP overrun is caused by data characters arriving at the port
    faster than they can be stored, or by the loss of a character due
    to a hardware malfunction.  This function is specific to the 884.
    """

    sub_function_code = 0x0013

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        count = _MCB.Counter.BusCharacterOverrun
        return ReturnIopOverrunCountResponse(count)


class ReturnIopOverrunCountResponse(DiagnosticBase):
    """Return Iop overrun count.

    The response data field returns the quantity of messages
    addressed to the slave that it could not handle due to an 884
    IOP overrun condition, since its last restart, clear counters
    operation, or power-up.
    """

    sub_function_code = 0x0013


class ClearOverrunCountRequest(DiagnosticBase):
    """Clear the overrun error counter and reset the error flag.

    An error flag should be cleared, but nothing else in the
    specification mentions is, so it is ignored.
    """

    sub_function_code = 0x0014

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
        """update_datastore the diagnostic request on the given device.

        :returns: The initialized response message
        """
        _MCB.Counter.BusCharacterOverrun = 0x0000
        return ClearOverrunCountResponse(self.message)


class ClearOverrunCountResponse(DiagnosticBase):
    """Clear the overrun error counter and reset the error flag."""

    sub_function_code = 0x0014


class GetClearModbusPlusRequest(DiagnosticBase):
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

    async def update_datastore(self, _context: ModbusSlaveContext) -> ModbusPDU:
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


class GetClearModbusPlusResponse(DiagnosticBase):
    """Return a series of 54 16-bit words (108 bytes) in the data field of the response.

    This function differs from the usual two-byte length of the data field.
    The data contains the statistics for the Modbus Plus peer processor in the slave device.
    """

    sub_function_code = 0x0015
