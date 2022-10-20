"""Bit Writing Request/Response.

TODO write mask request/response
"""
# pylint: disable=missing-type-doc
import struct

from pymodbus.constants import ModbusStatus
from pymodbus.pdu import ModbusExceptions as merror
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.utilities import pack_bitstring, unpack_bitstring


# ---------------------------------------------------------------------------#
#  Local Constants
# ---------------------------------------------------------------------------#
#  These are defined in the spec to turn a coil on/off
# ---------------------------------------------------------------------------#
_turn_coil_on = struct.pack(">H", ModbusStatus.On)
_turn_coil_off = struct.pack(">H", ModbusStatus.Off)


class WriteSingleCoilRequest(ModbusRequest):
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

    def __init__(self, address=None, value=None, unit=None, **kwargs):
        """Initialize a new instance.

        :param address: The variable address to write
        :param value: The value to write at address
        """
        ModbusRequest.__init__(self, unit=unit, **kwargs)
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
        self.value = value == ModbusStatus.On

    def execute(self, context):
        """Run a write coil request against a datastore.

        :param context: The datastore to request from
        :returns: The populated response or exception message
        """
        # if self.value not in [ModbusStatus.Off, ModbusStatus.On]:
        #    return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, 1):
            return self.doException(merror.IllegalAddress)

        context.setValues(self.function_code, self.address, [self.value])
        values = context.getValues(self.function_code, self.address, 1)
        return WriteSingleCoilResponse(self.address, values[0])

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Output Address (2 byte) + Output Value  (2 Bytes)
        :return:
        """
        return 1 + 2 + 2

    def __str__(self):
        """Return a string representation of the instance.

        :return: A string representation of the instance
        """
        return f"WriteCoilRequest({self.address}, {self.value}) => "


class WriteSingleCoilResponse(ModbusResponse):
    """The normal response is an echo of the request.

    Returned after the coil state has been written.
    """

    function_code = 5
    _rtu_frame_size = 8

    def __init__(self, address=None, value=None, **kwargs):
        """Initialize a new instance.

        :param address: The variable address written to
        :param value: The value written at address
        """
        ModbusResponse.__init__(self, **kwargs)
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
        self.value = value == ModbusStatus.On

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"WriteCoilResponse({self.address}) => {self.value}"


class WriteMultipleCoilsRequest(ModbusRequest):
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

    def __init__(self, address=None, values=None, unit=None, **kwargs):
        """Initialize a new instance.

        :param address: The starting request address
        :param values: The values to write
        """
        ModbusRequest.__init__(self, unit=unit, **kwargs)
        self.address = address
        if not values:
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

    def execute(self, context):
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

        context.setValues(self.function_code, self.address, self.values)
        return WriteMultipleCoilsResponse(self.address, count)

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        params = (self.address, len(self.values))
        return (
            "WriteNCoilRequest (%d) => %d "  # pylint: disable=consider-using-f-string
            % params
        )

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Output Address (2 byte) + Quantity of Outputs  (2 Bytes)
        :return:
        """
        return 1 + 2 + 2


class WriteMultipleCoilsResponse(ModbusResponse):
    """The normal response returns the function code.

    Starting address, and quantity of coils forced.
    """

    function_code = 15
    _rtu_frame_size = 8

    def __init__(self, address=None, count=None, **kwargs):
        """Initialize a new instance.

        :param address: The starting variable address written to
        :param count: The number of values written
        """
        ModbusResponse.__init__(self, **kwargs)
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
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"WriteNCoilResponse({self.address}, {self.count})"


# ---------------------------------------------------------------------------#
#  Exported symbols
# ---------------------------------------------------------------------------#
__all__ = [
    "WriteSingleCoilRequest",
    "WriteSingleCoilResponse",
    "WriteMultipleCoilsRequest",
    "WriteMultipleCoilsResponse",
]
