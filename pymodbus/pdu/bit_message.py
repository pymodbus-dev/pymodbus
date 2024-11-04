"""Bit Reading Request/Response messages."""

import struct
from typing import cast

from pymodbus.constants import ModbusStatus
from pymodbus.datastore import ModbusSlaveContext
from pymodbus.pdu.pdu import ModbusExceptions as merror
from pymodbus.pdu.pdu import ModbusPDU
from pymodbus.utilities import pack_bitstring, unpack_bitstring


class ReadCoilsRequest(ModbusPDU):
    """ReadCoilsRequest."""

    rtu_frame_size = 8
    function_code = 1

    def encode(self) -> bytes:
        """Encode a request pdu."""
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data: bytes) -> None:
        """Decode a request pdu."""
        self.address, self.count = struct.unpack(">HH", data)

    def get_response_pdu_size(self) -> int:
        """Get response pdu size.

        Func_code (1 byte) + Byte Count(1 byte) + Quantity of Coils (n Bytes)/8,
        if the remainder is different of 0 then N = N+1
        """
        return 1 + 1 + (self.count + 7) // 8

    async def update_datastore(self, context: ModbusSlaveContext) -> ModbusPDU:
        """Run request against a datastore."""
        if not (1 <= self.count <= 0x7D0):
            return self.doException(merror.ILLEGAL_VALUE)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.ILLEGAL_ADDRESS)
        values = cast(list[bool], await context.async_getValues(
            self.function_code, self.address, self.count
        ))
        response = (ReadCoilsResponse if self.function_code == 1 else ReadDiscreteInputsResponse)()
        response.bits = values
        return response


class ReadDiscreteInputsRequest(ReadCoilsRequest):
    """ReadDiscreteInputsRequest."""

    function_code = 2


class ReadCoilsResponse(ModbusPDU):
    """ReadCoilsResponse."""

    function_code = 1
    rtu_byte_count_pos = 2

    def encode(self) -> bytes:
        """Encode response pdu."""
        result = pack_bitstring(self.bits)
        packet = struct.pack(">B", len(result)) + pack_bitstring(self.bits)
        return packet

    def decode(self, data):
        """Decode response pdu."""
        self.bits = unpack_bitstring(data[1:])


class ReadDiscreteInputsResponse(ReadCoilsResponse):
    """ReadDiscreteInputsResponse."""

    function_code = 2


class WriteSingleCoilResponse(ModbusPDU):
    """WriteSingleCoilResponse."""

    function_code = 5
    rtu_frame_size = 8

    def encode(self) -> bytes:
        """Encode write coil request."""
        val = ModbusStatus.ON if self.bits[0] else ModbusStatus.OFF
        return struct.pack(">HH", self.address, val)

    def decode(self, data: bytes) -> None:
        """Decode a write coil request."""
        self.address, value = struct.unpack(">HH", data)
        self.bits = [value == ModbusStatus.ON]


class WriteSingleCoilRequest(WriteSingleCoilResponse):
    """WriteSingleCoilRequest."""

    async def update_datastore(self, context: ModbusSlaveContext) -> ModbusPDU:
        """Run a request against a datastore."""
        if not context.validate(self.function_code, self.address, 1):
            return self.doException(merror.ILLEGAL_ADDRESS)

        await context.async_setValues(self.function_code, self.address, self.bits)
        values = cast(list[bool], await context.async_getValues(self.function_code, self.address, 1))
        return WriteSingleCoilResponse(address=self.address, bits=values, slave_id=self.slave_id, transaction_id=self.transaction_id)

    def get_response_pdu_size(self) -> int:
        """Get response pdu size.

        Func_code (1 byte) + Output Address (2 byte) + Output Value  (2 Bytes)
        """
        return 1 + 2 + 2


class WriteMultipleCoilsRequest(ModbusPDU):
    """WriteMultipleCoilsRequest."""

    function_code = 15
    rtu_byte_count_pos = 6

    def encode(self) -> bytes:
        """Encode write coils request."""
        count = len(self.bits)
        byte_count = (count + 7) // 8
        packet = struct.pack(">HHB", self.address, count, byte_count)
        packet += pack_bitstring(self.bits)
        return packet

    def decode(self, data: bytes) -> None:
        """Decode a write coils request."""
        self.address, count, _ = struct.unpack(">HHB", data[0:5])
        values = unpack_bitstring(data[5:])
        self.bits = values[:count]

    async def update_datastore(self, context: ModbusSlaveContext) -> ModbusPDU:
        """Run a request against a datastore."""
        count = len(self.bits)
        if not 1 <= count <= 0x07B0:
            return self.doException(merror.ILLEGAL_VALUE)
        if not context.validate(self.function_code, self.address, count):
            return self.doException(merror.ILLEGAL_ADDRESS)

        await context.async_setValues(
            self.function_code, self.address, self.bits
        )
        return WriteMultipleCoilsResponse(address=self.address, count=count, slave_id=self.slave_id, transaction_id=self.transaction_id)

    def get_response_pdu_size(self) -> int:
        """Get response pdu size.

        Func_code (1 byte) + Output Address (2 byte) + Quantity of Outputs  (2 Bytes)
        :return:
        """
        return 1 + 2 + 2


class WriteMultipleCoilsResponse(ModbusPDU):
    """WriteMultipleCoilsResponse."""

    function_code = 15
    rtu_frame_size = 8

    def encode(self) -> bytes:
        """Encode write coils response."""
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data: bytes) -> None:
        """Decode a write coils response."""
        self.address, self.count = struct.unpack(">HH", data)
