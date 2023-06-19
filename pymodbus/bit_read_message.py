"""Bit Reading Request/Response messages."""

__all__ = [
    "ReadBitsResponseBase",
    "ReadCoilsRequest",
    "ReadCoilsResponse",
    "ReadDiscreteInputsRequest",
    "ReadDiscreteInputsResponse",
]

# pylint: disable=missing-type-doc
import struct

from pymodbus.pdu import ExceptionResponse, ModbusRequest, ModbusResponse
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.utilities import pack_bitstring, unpack_bitstring


class ReadBitsRequestBase(ModbusRequest):
    """Base class for Messages Requesting bit values."""

    _rtu_frame_size = 8

    def __init__(self, address, count, slave=0, **kwargs):
        """Initialize the read request data.

        :param address: The start address to read from
        :param count: The number of bits after "address" to read
        :param slave: Modbus slave slave ID
        """
        ModbusRequest.__init__(self, slave, **kwargs)
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
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"ReadBitRequest({self.address},{self.count})"


class ReadBitsResponseBase(ModbusResponse):
    """Base class for Messages responding to bit-reading values.

    The requested bits can be found in the .bits list.
    """

    _rtu_byte_count_pos = 2

    def __init__(self, values, slave=0, **kwargs):
        """Initialize a new instance.

        :param values: The requested values to be returned
        :param slave: Modbus slave slave ID
        """
        ModbusResponse.__init__(self, slave, **kwargs)

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

    def setBit(self, address, value=1):
        """Set the specified bit.

        :param address: The bit to set
        :param value: The value to set the bit to
        """
        self.bits[address] = bool(value)

    def resetBit(self, address):
        """Set the specified bit to 0.

        :param address: The bit to reset
        """
        self.setBit(address, 0)

    def getBit(self, address):
        """Get the specified bit's value.

        :param address: The bit to query
        :returns: The value of the requested bit
        """
        return self.bits[address]

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"{self.__class__.__name__}({len(self.bits)})"


class ReadCoilsRequest(ReadBitsRequestBase):
    """This function code is used to read from 1 to 2000(0x7d0) contiguous status of coils in a remote device.

    The Request PDU specifies the starting
    address, ie the address of the first coil specified, and the number of
    coils. In the PDU Coils are addressed starting at zero. Therefore coils
    numbered 1-16 are addressed as 0-15.
    """

    function_code = 1
    function_code_name = "read_coils"

    def __init__(self, address=None, count=None, slave=0, **kwargs):
        """Initialize a new instance.

        :param address: The address to start reading from
        :param count: The number of bits to read
        :param slave: Modbus slave slave ID
        """
        ReadBitsRequestBase.__init__(self, address, count, slave, **kwargs)

    def execute(self, context):
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
        values = context.getValues(self.function_code, self.address, self.count)
        if isinstance(values, ExceptionResponse):
            return values
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

    def __init__(self, values=None, slave=0, **kwargs):
        """Initialize a new instance.

        :param values: The request values to respond with
        :param slave: Modbus slave slave ID
        """
        ReadBitsResponseBase.__init__(self, values, slave, **kwargs)


class ReadDiscreteInputsRequest(ReadBitsRequestBase):
    """This function code is used to read from 1 to 2000(0x7d0).

    Contiguous status of discrete inputs in a remote device. The Request PDU specifies the
    starting address, ie the address of the first input specified, and the
    number of inputs. In the PDU Discrete Inputs are addressed starting at
    zero. Therefore Discrete inputs numbered 1-16 are addressed as 0-15.
    """

    function_code = 2
    function_code_name = "read_discrete_input"

    def __init__(self, address=None, count=None, slave=0, **kwargs):
        """Initialize a new instance.

        :param address: The address to start reading from
        :param count: The number of bits to read
        :param slave: Modbus slave slave ID
        """
        ReadBitsRequestBase.__init__(self, address, count, slave, **kwargs)

    def execute(self, context):
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
        values = context.getValues(self.function_code, self.address, self.count)
        if isinstance(values, ExceptionResponse):
            return values
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

    def __init__(self, values=None, slave=0, **kwargs):
        """Initialize a new instance.

        :param values: The request values to respond with
        :param slave: Modbus slave slave ID
        """
        ReadBitsResponseBase.__init__(self, values, slave, **kwargs)
