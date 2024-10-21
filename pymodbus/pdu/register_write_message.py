"""Register Writing Request/Response Messages."""


# pylint: disable=missing-type-doc
import struct

from pymodbus.pdu.pdu import ModbusExceptions as merror
from pymodbus.pdu.pdu import ModbusPDU


class WriteSingleRegisterRequest(ModbusPDU):
    """This function code is used to write a single holding register in a remote device.

    The Request PDU specifies the address of the register to
    be written. Registers are addressed starting at zero. Therefore register
    numbered 1 is addressed as 0.
    """

    function_code = 6
    function_code_name = "write_register"
    _rtu_frame_size = 8

    def __init__(self, address=None, value=None, slave=None, transaction=0, skip_encode=0):
        """Initialize a new instance.

        :param address: The address to start writing add
        :param value: The values to write
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.address = address
        self.value = value

    def encode(self):
        """Encode a write single register packet packet request.

        :returns: The encoded packet
        """
        packet = struct.pack(">H", self.address)
        if self.skip_encode or isinstance(self.value, bytes):  # pragma: no cover
            packet += self.value  # pragma: no cover
        else:
            packet += struct.pack(">H", self.value)
        return packet

    def decode(self, data):
        """Decode a write single register packet packet request.

        :param data: The request to decode
        """
        self.address, self.value = struct.unpack(">HH", data)

    async def update_datastore(self, context):  # pragma: no cover
        """Run a write single register request against a datastore.

        :param context: The datastore to request from
        :returns: An initialized response, exception message otherwise
        """
        if not 0 <= self.value <= 0xFFFF:
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, 1):
            return self.doException(merror.IllegalAddress)

        await context.async_setValues(
            self.function_code, self.address, [self.value]
        )
        values = await context.async_getValues(self.function_code, self.address, 1)
        return WriteSingleRegisterResponse(self.address, values[0])

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Register Address(2 byte) + Register Value (2 bytes)
        :return:
        """
        return 1 + 2 + 2

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"WriteRegisterRequest {self.address}"


class WriteSingleRegisterResponse(ModbusPDU):
    """The normal response is an echo of the request.

    Returned after the register contents have been written.
    """

    function_code = 6
    _rtu_frame_size = 8

    def __init__(self, address=0, value=0, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param address: The address to start writing add
        :param value: The values to write
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.address = address
        self.value = value

    def encode(self):
        """Encode a write single register packet packet request.

        :returns: The encoded packet
        """
        return struct.pack(">HH", self.address, self.value)

    def decode(self, data):
        """Decode a write single register packet packet request.

        :param data: The request to decode
        """
        self.address, self.value = struct.unpack(">HH", data)

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Starting Address (2 byte) + And_mask (2 Bytes) + OrMask (2 Bytes)
        :return:
        """
        return 1 + 2 + 2 + 2

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        params = (self.address, self.value)
        return (
            "WriteRegisterResponse %d => %d"  # pylint: disable=consider-using-f-string
            % params
        )


# ---------------------------------------------------------------------------#
#  Write Multiple Registers
# ---------------------------------------------------------------------------#
class WriteMultipleRegistersRequest(ModbusPDU):
    """This function code is used to write a block.

    Of contiguous registers (1 to approx. 120 registers) in a remote device.

    The requested written values are specified in the request data field.
    Data is packed as two bytes per register.
    """

    function_code = 16
    function_code_name = "write_registers"
    _rtu_byte_count_pos = 6
    _pdu_length = 5  # func + adress1 + adress2 + outputQuant1 + outputQuant2

    def __init__(self, address=0, values=None, slave=None, transaction=0, skip_encode=0):
        """Initialize a new instance.

        :param address: The address to start writing to
        :param values: The values to write
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.address = address
        if values is None:
            values = []
        elif not hasattr(values, "__iter__"):
            values = [values]
        self.values = values
        self.count = len(self.values)
        self.byte_count = self.count * 2

    def encode(self):
        """Encode a write single register packet packet request.

        :returns: The encoded packet
        """
        packet = struct.pack(">HHB", self.address, self.count, self.byte_count)
        if self.skip_encode:  # pragma: no cover
            return packet + b"".join(self.values)  # pragma: no cover

        for value in self.values:
            if isinstance(value, bytes):  # pragma: no cover
                packet += value  # pragma: no cover
            else:
                packet += struct.pack(">H", value)

        return packet

    def decode(self, data):
        """Decode a write single register packet packet request.

        :param data: The request to decode
        """
        self.address, self.count, self.byte_count = struct.unpack(">HHB", data[:5])
        self.values = []  # reset
        for idx in range(5, (self.count * 2) + 5, 2):
            self.values.append(struct.unpack(">H", data[idx : idx + 2])[0])

    async def update_datastore(self, context):  # pragma: no cover
        """Run a write single register request against a datastore.

        :param context: The datastore to request from
        :returns: An initialized response, exception message otherwise
        """
        if not 1 <= self.count <= 0x07B:
            return self.doException(merror.IllegalValue)
        if self.byte_count != self.count * 2:
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)

        await context.async_setValues(
            self.function_code, self.address, self.values
        )
        return WriteMultipleRegistersResponse(self.address, self.count)

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Starting Address (2 byte) + Quantity of Registers  (2 Bytes)
        :return:
        """
        return 1 + 2 + 2

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        params = (self.address, self.count)
        return (
            "WriteMultipleRegisterRequest %d => %d"  # pylint: disable=consider-using-f-string
            % params
        )


class WriteMultipleRegistersResponse(ModbusPDU):
    """The normal response returns the function code.

    Starting address, and quantity of registers written.
    """

    function_code = 16
    _rtu_frame_size = 8

    def __init__(self, address=0, count=0, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param address: The address to start writing to
        :param count: The number of registers to write to
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.address = address
        self.count = count

    def encode(self):
        """Encode a write single register packet packet request.

        :returns: The encoded packet
        """
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data):
        """Decode a write single register packet packet request.

        :param data: The request to decode
        """
        self.address, self.count = struct.unpack(">HH", data)

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        params = (self.address, self.count)
        return (
            "WriteMultipleRegisterResponse (%d,%d)"  # pylint: disable=consider-using-f-string
            % params
        )


class MaskWriteRegisterRequest(ModbusPDU):
    """This function code is used to modify the contents.

    Of a specified holding register using a combination of an AND mask,
    an OR mask, and the register's current contents.
    The function can be used to set or clear individual bits in the register.
    """

    function_code = 0x16
    function_code_name = "mask_write_register"
    _rtu_frame_size = 10

    def __init__(self, address=0x0000, and_mask=0xFFFF, or_mask=0x0000, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param address: The mask pointer address (0x0000 to 0xffff)
        :param and_mask: The and bitmask to apply to the register address
        :param or_mask: The or bitmask to apply to the register address
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.address = address
        self.and_mask = and_mask
        self.or_mask = or_mask

    def encode(self):
        """Encode the request packet.

        :returns: The byte encoded packet
        """
        return struct.pack(">HHH", self.address, self.and_mask, self.or_mask)

    def decode(self, data):
        """Decode the incoming request.

        :param data: The data to decode into the address
        """
        self.address, self.and_mask, self.or_mask = struct.unpack(">HHH", data)

    async def update_datastore(self, context):  # pragma: no cover
        """Run a mask write register request against the store.

        :param context: The datastore to request from
        :returns: The populated response
        """
        if not 0x0000 <= self.and_mask <= 0xFFFF:
            return self.doException(merror.IllegalValue)
        if not 0x0000 <= self.or_mask <= 0xFFFF:
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, 1):
            return self.doException(merror.IllegalAddress)
        values = (await context.async_getValues(self.function_code, self.address, 1))[0]
        values = (values & self.and_mask) | (self.or_mask & ~self.and_mask)
        await context.async_setValues(
            self.function_code, self.address, [values]
        )
        return MaskWriteRegisterResponse(self.address, self.and_mask, self.or_mask)


class MaskWriteRegisterResponse(ModbusPDU):
    """The normal response is an echo of the request.

    The response is returned after the register has been written.
    """

    function_code = 0x16
    _rtu_frame_size = 10

    def __init__(self, address=0x0000, and_mask=0xFFFF, or_mask=0x0000, slave=1, transaction=0, skip_encode=False):
        """Initialize new instance.

        :param address: The mask pointer address (0x0000 to 0xffff)
        :param and_mask: The and bitmask applied to the register address
        :param or_mask: The or bitmask applied to the register address
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.address = address
        self.and_mask = and_mask
        self.or_mask = or_mask

    def encode(self):
        """Encode the response.

        :returns: The byte encoded message
        """
        return struct.pack(">HHH", self.address, self.and_mask, self.or_mask)

    def decode(self, data):
        """Decode a the response.

        :param data: The packet data to decode
        """
        self.address, self.and_mask, self.or_mask = struct.unpack(">HHH", data)
