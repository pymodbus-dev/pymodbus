"""Bit Reading Request/Response messages."""

# pylint: disable=missing-type-doc
import struct

from pymodbus.constants import ModbusStatus
from pymodbus.pdu.pdu import ModbusExceptions as merror
from pymodbus.pdu.pdu import ModbusPDU
from pymodbus.utilities import pack_bitstring, unpack_bitstring


_turn_coil_on = struct.pack(">H", ModbusStatus.ON)
_turn_coil_off = struct.pack(">H", ModbusStatus.OFF)


class ReadBitsRequestBase(ModbusPDU):
    """Base class for Messages Requesting bit values."""

    _rtu_frame_size = 8

    def __init__(self, address, count, slave, transaction, skip_encode):
        """Initialize the read request data.

        :param address: The start address to read from
        :param count: The number of bits after "address" to read
        :param slave: Modbus slave slave ID
        """
        super().__init__()
        super().setBaseData(slave, transaction, skip_encode)
        self.address = address
        self.count = count

    def encode(self):
        """Encode a request pdu.

        :returns: The encoded pdu
        """
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data):
        """Decode a request pdu.

        :param data: The packet data to decode
        """
        self.address, self.count = struct.unpack(">HH", data)

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Byte Count(1 byte) + Quantity of Coils (n Bytes)/8,
        if the remainder is different of 0 then N = N+1
        :return:
        """
        count = self.count // 8
        if self.count % 8:
            count += 1

        return 1 + 1 + count

    def __str__(self):
        """Return a string representation of the instance."""
        return f"ReadBitRequest({self.address},{self.count})"


class ReadBitsResponseBase(ModbusPDU):
    """Base class for Messages responding to bit-reading values.

    The requested bits can be found in the .bits list.
    """

    _rtu_byte_count_pos = 2

    def __init__(self, values, slave, transaction, skip_encode):
        """Initialize a new instance.

        :param values: The requested values to be returned
        :param slave: Modbus slave slave ID
        """
        super().__init__()
        super().setBaseData(slave, transaction, skip_encode)

        #: A list of booleans representing bit values
        self.bits = values or []

    def encode(self):
        """Encode response pdu.

        :returns: The encoded packet message
        """
        result = pack_bitstring(self.bits)
        packet = struct.pack(">B", len(result)) + result
        return packet

    def decode(self, data):
        """Decode response pdu.

        :param data: The packet data to decode
        """
        self.byte_count = int(data[0])  # pylint: disable=attribute-defined-outside-init
        self.bits = unpack_bitstring(data[1:])

    def __str__(self):
        """Return a string representation of the instance."""
        return f"{self.__class__.__name__}({len(self.bits)})"


class ReadCoilsRequest(ReadBitsRequestBase):
    """This function code is used to read from 1 to 2000(0x7d0) contiguous status of coils in a remote device.

    The Request PDU specifies the starting
    address, ie the address of the first coil specified, and the number of
    coils. In the PDU Coils are addressed starting at zero. Therefore coils
    numbered 1-16 are addressed as 0-15.
    """

    function_code = 1

    def __init__(self, address=None, count=None, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param address: The address to start reading from
        :param count: The number of bits to read
        :param slave: Modbus slave slave ID
        """
        ReadBitsRequestBase.__init__(self, address, count, slave, transaction, skip_encode)

    async def update_datastore(self, context):
        """Run a read coils request against a datastore.

        Before running the request, we make sure that the request is in
        the max valid range (0x001-0x7d0). Next we make sure that the
        request is valid against the current datastore.

        :param context: The datastore to request from
        :returns: An initialized :py:class:`~pymodbus.register_read_message.ReadCoilsResponse`, or an :py:class:`~pymodbus.pdu.ExceptionResponse` if an error occurred
        """
        if not (1 <= self.count <= 0x7D0):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = await context.async_getValues(
            self.function_code, self.address, self.count
        )
        return ReadCoilsResponse(values)


class ReadCoilsResponse(ReadBitsResponseBase):
    """The coils in the response message are packed as one coil per bit of the data field.

    Status is indicated as 1= ON and 0= OFF. The LSB of the
    first data byte contains the output addressed in the query. The other
    coils follow toward the high order end of this byte, and from low order
    to high order in subsequent bytes.

    If the returned output quantity is not a multiple of eight, the
    remaining bits in the final data byte will be padded with zeros
    (toward the high order end of the byte). The Byte Count field specifies
    the quantity of complete bytes of data.

    The requested coils can be found in boolean form in the .bits list.
    """

    function_code = 1

    def __init__(self, values=None, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param values: The request values to respond with
        :param slave: Modbus slave slave ID
        """
        ReadBitsResponseBase.__init__(self, values, slave, transaction, skip_encode)


class ReadDiscreteInputsRequest(ReadBitsRequestBase):
    """This function code is used to read from 1 to 2000(0x7d0).

    Contiguous status of discrete inputs in a remote device. The Request PDU specifies the
    starting address, ie the address of the first input specified, and the
    number of inputs. In the PDU Discrete Inputs are addressed starting at
    zero. Therefore Discrete inputs numbered 1-16 are addressed as 0-15.
    """

    function_code = 2

    def __init__(self, address=None, count=None, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param address: The address to start reading from
        :param count: The number of bits to read
        :param slave: Modbus slave slave ID
        """
        ReadBitsRequestBase.__init__(self, address, count, slave, transaction, skip_encode)

    async def update_datastore(self, context):
        """Run a read discrete input request against a datastore.

        Before running the request, we make sure that the request is in
        the max valid range (0x001-0x7d0). Next we make sure that the
        request is valid against the current datastore.

        :param context: The datastore to request from
        :returns: An initialized :py:class:`~pymodbus.register_read_message.ReadDiscreteInputsResponse`, or an :py:class:`~pymodbus.pdu.ExceptionResponse` if an error occurred
        """
        if not (1 <= self.count <= 0x7D0):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = await context.async_getValues(
            self.function_code, self.address, self.count
        )
        return ReadDiscreteInputsResponse(values)


class ReadDiscreteInputsResponse(ReadBitsResponseBase):
    """The discrete inputs in the response message are packed as one input per bit of the data field.

    Status is indicated as 1= ON; 0= OFF. The LSB of
    the first data byte contains the input addressed in the query. The other
    inputs follow toward the high order end of this byte, and from low order
    to high order in subsequent bytes.

    If the returned input quantity is not a multiple of eight, the
    remaining bits in the final data byte will be padded with zeros
    (toward the high order end of the byte). The Byte Count field specifies
    the quantity of complete bytes of data.

    The requested coils can be found in boolean form in the .bits list.
    """

    function_code = 2

    def __init__(self, values=None, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param values: The request values to respond with
        :param slave: Modbus slave slave ID
        """
        ReadBitsResponseBase.__init__(self, values, slave, transaction, skip_encode)


class WriteSingleCoilRequest(ModbusPDU):
    """This function code is used to write a single output to either ON or OFF in a remote device.

    The requested ON/OFF state is specified by a constant in the request
    data field. A value of FF 00 hex requests the output to be ON. A value
    of 00 00 requests it to be OFF. All other values are illegal and will
    not affect the output.

    The Request PDU specifies the address of the coil to be forced. Coils
    are addressed starting at zero. Therefore coil numbered 1 is addressed
    as 0. The requested ON/OFF state is specified by a constant in the Coil
    Value field. A value of 0XFF00 requests the coil to be ON. A value of
    0X0000 requests the coil to be off. All other values are illegal and
    will not affect the coil.
    """

    function_code = 5

    _rtu_frame_size = 8

    def __init__(self, address=None, value=None, slave=None, transaction=0, skip_encode=0):
        """Initialize a new instance.

        :param address: The variable address to write
        :param value: The value to write at address
        """
        super().__init__()
        super().setBaseData(slave, transaction, skip_encode)
        self.address = address
        self.value = bool(value)

    def encode(self):
        """Encode write coil request.

        :returns: The byte encoded message
        """
        result = struct.pack(">H", self.address)
        if self.value:
            result += _turn_coil_on
        else:
            result += _turn_coil_off
        return result

    def decode(self, data):
        """Decode a write coil request.

        :param data: The packet data to decode
        """
        self.address, value = struct.unpack(">HH", data)
        self.value = value == ModbusStatus.ON

    async def update_datastore(self, context):
        """Run a write coil request against a datastore.

        :param context: The datastore to request from
        :returns: The populated response or exception message
        """
        # if self.value not in [ModbusStatus.Off, ModbusStatus.On]:
        #    return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, 1):
            return self.doException(merror.IllegalAddress)

        await context.async_setValues(self.function_code, self.address, [self.value])
        values = await context.async_getValues(self.function_code, self.address, 1)
        return WriteSingleCoilResponse(self.address, values[0])

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Output Address (2 byte) + Output Value  (2 Bytes)
        :return:
        """
        return 1 + 2 + 2

    def __str__(self):
        """Return a string representation of the instance."""
        return f"WriteCoilRequest({self.address}, {self.value}) => "


class WriteSingleCoilResponse(ModbusPDU):
    """The normal response is an echo of the request.

    Returned after the coil state has been written.
    """

    function_code = 5
    _rtu_frame_size = 8

    def __init__(self, address=None, value=None, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param address: The variable address written to
        :param value: The value written at address
        """
        super().__init__()
        super().setBaseData(slave, transaction, skip_encode)
        self.address = address
        self.value = value

    def encode(self):
        """Encode write coil response.

        :return: The byte encoded message
        """
        result = struct.pack(">H", self.address)
        if self.value:
            result += _turn_coil_on
        else:
            result += _turn_coil_off
        return result

    def decode(self, data):
        """Decode a write coil response.

        :param data: The packet data to decode
        """
        self.address, value = struct.unpack(">HH", data)
        self.value = value == ModbusStatus.ON

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"WriteCoilResponse({self.address}) => {self.value}"


class WriteMultipleCoilsRequest(ModbusPDU):
    """This function code is used to forcea sequence of coils.

    To either ON or OFF in a remote device. The Request PDU specifies the coil
    references to be forced. Coils are addressed starting at zero. Therefore
    coil numbered 1 is addressed as 0.

    The requested ON/OFF states are specified by contents of the request
    data field. A logical "1" in a bit position of the field requests the
    corresponding output to be ON. A logical "0" requests it to be OFF."
    """

    function_code = 15
    _rtu_byte_count_pos = 6

    def __init__(self, address=0, values=None, slave=None, transaction=0, skip_encode=0):
        """Initialize a new instance.

        :param address: The starting request address
        :param values: The values to write
        """
        super().__init__()
        super().setBaseData(slave, transaction, skip_encode)
        self.address = address
        if values is None:
            values = []
        elif not hasattr(values, "__iter__"):
            values = [values]
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
        return f"WriteNCoilRequest ({self.address}) => {len(self.values)}"

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
    _rtu_frame_size = 8

    def __init__(self, address=None, count=None, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param address: The starting variable address written to
        :param count: The number of values written
        """
        super().__init__()
        super().setBaseData(slave, transaction, skip_encode)
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
        return f"WriteNCoilResponse({self.address}, {self.count})"
