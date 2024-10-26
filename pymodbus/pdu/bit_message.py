"""Bit Reading Request/Response messages."""

# pylint: disable=missing-type-doc
import struct
from typing import cast

from pymodbus.constants import ModbusStatus
from pymodbus.datastore import ModbusSlaveContext
from pymodbus.pdu.pdu import ModbusExceptions as merror
from pymodbus.pdu.pdu import ModbusPDU
from pymodbus.utilities import pack_bitstring, unpack_bitstring


_turn_coil_on = struct.pack(">H", ModbusStatus.ON)
_turn_coil_off = struct.pack(">H", ModbusStatus.OFF)


class ReadCoilsRequest(ModbusPDU):
    """ReadCoilsRequest."""

    rtu_frame_size = 8
    function_code = 1

    def __init__(self) -> None:
        """Initialize the read request."""
        super().__init__()
        self.address: int = 0
        self.count: int = 0

    def setData(self, address: int, count: int, slave_id: int, transaction_id: int) -> None:
        """Set data."""
        super().setBaseData(slave_id, transaction_id)
        self.address = address
        self.count = count

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
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = cast(list[bool], await context.async_getValues(
            self.function_code, self.address, self.count
        ))
        response = (ReadCoilsResponse if self.function_code == 1 else ReadDiscreteInputsResponse)()
        response.setData(values, self.slave_id, self.transaction_id)
        return response


    def __str__(self) -> str:
        """Return a string representation of the instance."""
        return f"{self.__class__.__name__}({self.address},{self.count})"


class ReadDiscreteInputsRequest(ReadCoilsRequest):
    """ReadDiscreteInputsRequest."""

    function_code = 2


class ReadCoilsResponse(ModbusPDU):
    """ReadCoilsResponse."""

    function_code = 1
    rtu_byte_count_pos = 2

    def setData(self, values: list[bool], slave_id: int, transaction_id: int) -> None:
        """Set data."""
        super().setBaseData(slave_id, transaction_id)
        self.bits = values

    def encode(self) -> bytes:
        """Encode response pdu."""
        result = pack_bitstring(self.bits)
        packet = struct.pack(">B", len(result)) + pack_bitstring(self.bits)
        return packet

    def decode(self, data):
        """Decode response pdu."""
        self.bits = unpack_bitstring(data[1:])

    def __str__(self):
        """Return a string representation of the instance."""
        return f"{self.__class__.__name__}({len(self.bits)})"


class ReadDiscreteInputsResponse(ReadCoilsResponse):
    """ReadDiscreteInputsResponse."""

    function_code = 2


class WriteSingleCoilResponse(ModbusPDU):
    """WriteSingleCoilResponse."""

    function_code = 5
    rtu_frame_size = 8

    def __init__(self) -> None:
        """Instancitate object."""
        super().__init__()
        self.address: int = 0
        self.value: bool = False

    def setData(self, address: int, value: bool, slave_id: int, transaction_id: int) -> None:
        """Set data."""
        super().setBaseData(slave_id, transaction_id)
        self.address = address
        self.value = value

    def encode(self) -> bytes:
        """Encode write coil request."""
        val = ModbusStatus.ON if self.value else ModbusStatus.OFF
        return struct.pack(">HH", self.address, val)

    def decode(self, data: bytes) -> None:
        """Decode a write coil request."""
        self.address, value = struct.unpack(">HH", data)
        self.value = value == ModbusStatus.ON

    def __str__(self) -> str:
        """Return a string representation of the instance."""
        return f"{self.__class__.__name__}({self.address}) => {self.value}"


class WriteSingleCoilRequest(WriteSingleCoilResponse):
    """WriteSingleCoilRequest."""

    async def update_datastore(self, context: ModbusSlaveContext) -> ModbusPDU:
        """Run a request against a datastore."""
        if not context.validate(self.function_code, self.address, 1):
            return self.doException(merror.IllegalAddress)

        await context.async_setValues(self.function_code, self.address, [self.value])
        values = cast(list[bool], await context.async_getValues(self.function_code, self.address, 1))
        pdu = WriteSingleCoilResponse()
        pdu.setData(self.address, values[0], self.slave_id, self.transaction_id)
        return pdu

    def get_response_pdu_size(self) -> int:
        """Get response pdu size.

        Func_code (1 byte) + Output Address (2 byte) + Output Value  (2 Bytes)
        """
        return 1 + 2 + 2


class WriteMultipleCoilsRequest(WriteSingleCoilRequest):
    """This function code is used to forcea sequence of coils.

    To either ON or OFF in a remote device. The Request PDU specifies the coil
    references to be forced. Coils are addressed starting at zero. Therefore
    coil numbered 1 is addressed as 0.

    The requested ON/OFF states are specified by contents of the request
    data field. A logical "1" in a bit position of the field requests the
    corresponding output to be ON. A logical "0" requests it to be OFF."
    """

    function_code = 15
    rtu_byte_count_pos = 6

    def __init__(self, address=0, values=None, slave=None, transaction=0):
        """Initialize a new instance.

        :param address: The starting request address
        :param values: The values to write
        """
        super().__init__()
        super().setBaseData(slave, transaction)
        self.address = address
        if values is None:
            values = []
        elif not hasattr(values, "__iter__"):
            values = [values]
        for value in values:
            if value and not isinstance(value, bool):
                raise TypeError("NO BOOL")
        self.values = values
        self.byte_count = (len(self.values) + 7) // 8

    def encode(self):
        """Encode write coils request.

        :returns: The byte encoded message
        """
        count = len(self.values)
        self.byte_count = (count + 7) // 8
        packet = struct.pack(">HHB", self.address, count, self.byte_count)
        packet += pack_bitstring(self.values)
        return packet

    def decode(self, data):
        """Decode a write coils request.

        :param data: The packet data to decode
        """
        self.address, count, self.byte_count = struct.unpack(">HHB", data[0:5])
        values = unpack_bitstring(data[5:])
        self.values = values[:count]

    async def update_datastore(self, context):
        """Run a write coils request against a datastore.

        :param context: The datastore to request from
        :returns: The populated response or exception message
        """
        count = len(self.values)
        if not 1 <= count <= 0x07B0:
            return self.doException(merror.IllegalValue)
        if self.byte_count != (count + 7) // 8:
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, count):
            return self.doException(merror.IllegalAddress)

        await context.async_setValues(
            self.function_code, self.address, self.values
        )
        return WriteMultipleCoilsResponse(self.address, count)

    def __str__(self):
        """Return a string representation of the instance."""
        return f"{self.__class__.__name__}({self.address}) => {len(self.values)}"

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Output Address (2 byte) + Quantity of Outputs  (2 Bytes)
        :return:
        """
        return 1 + 2 + 2


class WriteMultipleCoilsResponse(ModbusPDU):
    """The normal response returns the function code.

    Starting address, and quantity of coils forced.
    """

    function_code = 15
    rtu_frame_size = 8

    def __init__(self, address=None, count=None, slave=1, transaction=0):
        """Initialize a new instance.

        :param address: The starting variable address written to
        :param count: The number of values written
        """
        super().__init__()
        super().setBaseData(slave, transaction)
        self.address = address
        self.count = count

    def encode(self):
        """Encode write coils response.

        :returns: The byte encoded message
        """
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data):
        """Decode a write coils response.

        :param data: The packet data to decode
        """
        self.address, self.count = struct.unpack(">HH", data)

    def __str__(self):
        """Return a string representation of the instance."""
        return f"{self.__class__.__name__}({self.address}, {self.count})"
