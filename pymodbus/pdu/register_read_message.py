"""Register Reading Request/Response."""


# pylint: disable=missing-type-doc
import struct

from pymodbus.exceptions import ModbusIOException
from pymodbus.pdu.pdu import ExceptionResponse, ModbusPDU
from pymodbus.pdu.pdu import ModbusExceptions as merror


class ReadRegistersRequestBase(ModbusPDU):
    """Base class for reading a modbus register."""

    _rtu_frame_size = 8

    def __init__(self, address, count, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param address: The address to start the read from
        :param count: The number of registers to read
        :param slave: Modbus slave slave ID
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.address = address
        self.count = count

    def encode(self):
        """Encode the request packet.

        :return: The encoded packet
        """
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data):
        """Decode a register request packet.

        :param data: The request to decode
        """
        self.address, self.count = struct.unpack(">HH", data)

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Byte Count(1 byte) + 2 * Quantity of Coils (n Bytes).
        """
        return 1 + 1 + 2 * self.count

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"{self.__class__.__name__} ({self.address},{self.count})"


class ReadRegistersResponseBase(ModbusPDU):
    """Base class for responding to a modbus register read.

    The requested registers can be found in the .registers list.
    """

    _rtu_byte_count_pos = 2

    def __init__(self, values, slave=1, transaction=0, skip_encode=False):
        """Initialize a new instance.

        :param values: The values to write to
        :param slave: Modbus slave slave ID
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)

        #: A list of register values
        self.registers = values or []

    def encode(self):
        """Encode the response packet.

        :returns: The encoded packet
        """
        result = struct.pack(">B", len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack(">H", register)
        return result

    def decode(self, data):
        """Decode a register response packet.

        :param data: The request to decode
        """
        byte_count = int(data[0])
        if byte_count < 2 or byte_count > 252 or byte_count % 2 == 1 or byte_count != len(data) - 1:  # pragma: no cover
            raise ModbusIOException(f"Invalid response {data} has byte count of {byte_count}")  # pragma: no cover
        self.registers = []
        for i in range(1, byte_count + 1, 2):
            self.registers.append(struct.unpack(">H", data[i : i + 2])[0])

    def getRegister(self, index):
        """Get the requested register.

        :param index: The indexed register to retrieve
        :returns: The request register
        """
        return self.registers[index]  # pragma: no cover

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"{self.__class__.__name__} ({len(self.registers)})"


class ReadHoldingRegistersRequest(ReadRegistersRequestBase):
    """Read holding registers.

    This function code is used to read the contents of a contiguous block
    of holding registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore registers numbered
    1-16 are addressed as 0-15.
    """

    function_code = 3
    function_code_name = "read_holding_registers"

    def __init__(self, address=None, count=None, slave=1, transaction=0, skip_encode=0):
        """Initialize a new instance of the request.

        :param address: The starting address to read from
        :param count: The number of registers to read from address
        :param slave: Modbus slave slave ID
        """
        super().__init__(address, count, slave, transaction, skip_encode)

    async def update_datastore(self, context):  # pragma: no cover
        """Run a read holding request against a datastore.

        :param context: The datastore to request from
        :returns: An initialized :py:class:`~pymodbus.register_read_message.ReadHoldingRegistersResponse`
        """
        if not (1 <= self.count <= 0x7D):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = await context.async_getValues(
            self.function_code, self.address, self.count
        )
        if isinstance(values, ExceptionResponse):
            return values
        return ReadHoldingRegistersResponse(values)


class ReadHoldingRegistersResponse(ReadRegistersResponseBase):
    """Read holding registers.

    This function code is used to read the contents of a contiguous block
    of holding registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore registers numbered
    1-16 are addressed as 0-15.

    The requested registers can be found in the .registers list.
    """

    function_code = 3

    def __init__(self, values=None, slave=None, transaction=0, skip_encode=0):
        """Initialize a new response instance.

        :param values: The resulting register values
        """
        super().__init__(values, slave, transaction, skip_encode)


class ReadInputRegistersRequest(ReadRegistersRequestBase):
    """Read input registers.

    This function code is used to read from 1 to approx. 125 contiguous
    input registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore input registers
    numbered 1-16 are addressed as 0-15.
    """

    function_code = 4
    function_code_name = "read_input_registers"

    def __init__(self, address=None, count=None, slave=1, transaction=0, skip_encode=0):
        """Initialize a new instance of the request.

        :param address: The starting address to read from
        :param count: The number of registers to read from address
        :param slave: Modbus slave slave ID
        """
        super().__init__(address, count, slave, transaction, skip_encode)

    async def update_datastore(self, context):  # pragma: no cover
        """Run a read input request against a datastore.

        :param context: The datastore to request from
        :returns: An initialized :py:class:`~pymodbus.register_read_message.ReadInputRegistersResponse`
        """
        if not (1 <= self.count <= 0x7D):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = await context.async_getValues(
            self.function_code, self.address, self.count
        )
        if isinstance(values, ExceptionResponse):
            return values
        return ReadInputRegistersResponse(values)


class ReadInputRegistersResponse(ReadRegistersResponseBase):
    """Read/write input registers.

    This function code is used to read from 1 to approx. 125 contiguous
    input registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore input registers
    numbered 1-16 are addressed as 0-15.

    The requested registers can be found in the .registers list.
    """

    function_code = 4

    def __init__(self, values=None, slave=None, transaction=0, skip_encode=0):
        """Initialize a new response instance.

        :param values: The resulting register values
        """
        super().__init__(values, slave, transaction, skip_encode)


class ReadWriteMultipleRegistersRequest(ModbusPDU):
    """Read/write multiple registers.

    This function code performs a combination of one read operation and one
    write operation in a single MODBUS transaction. The write
    operation is performed before the read.

    Holding registers are addressed starting at zero. Therefore holding
    registers 1-16 are addressed in the PDU as 0-15.

    The request specifies the starting address and number of holding
    registers to be read as well as the starting address, number of holding
    registers, and the data to be written. The byte count specifies the
    number of bytes to follow in the write data field."
    """

    function_code = 23
    function_code_name = "read_write_multiple_registers"
    _rtu_byte_count_pos = 10

    def __init__(self, read_address=0x00, read_count=0, write_address=0x00, write_registers=None, slave=1, transaction=0, skip_encode=False):
        """Initialize a new request message.

        :param read_address: The address to start reading from
        :param read_count: The number of registers to read from address
        :param write_address: The address to start writing to
        :param write_registers: The registers to write to the specified address
        """
        super().__init__()
        super().setData(slave, transaction, skip_encode)
        self.read_address = read_address
        self.read_count = read_count
        self.write_address = write_address
        self.write_registers = write_registers
        if not hasattr(self.write_registers, "__iter__"):
            self.write_registers = [self.write_registers]
        self.write_count = len(self.write_registers)
        self.write_byte_count = self.write_count * 2

    def encode(self):
        """Encode the request packet.

        :returns: The encoded packet
        """
        result = struct.pack(
            ">HHHHB",
            self.read_address,
            self.read_count,
            self.write_address,
            self.write_count,
            self.write_byte_count,
        )
        for register in self.write_registers:
            result += struct.pack(">H", register)
        return result

    def decode(self, data):
        """Decode the register request packet.

        :param data: The request to decode
        """
        (
            self.read_address,
            self.read_count,
            self.write_address,
            self.write_count,
            self.write_byte_count,
        ) = struct.unpack(">HHHHB", data[:9])
        self.write_registers = []
        for i in range(9, self.write_byte_count + 9, 2):
            register = struct.unpack(">H", data[i : i + 2])[0]
            self.write_registers.append(register)

    async def update_datastore(self, context):  # pragma: no cover
        """Run a write single register request against a datastore.

        :param context: The datastore to request from
        :returns: An initialized :py:class:`~pymodbus.register_read_message.ReadWriteMultipleRegistersResponse`
        """
        if not (1 <= self.read_count <= 0x07D):
            return self.doException(merror.IllegalValue)
        if not 1 <= self.write_count <= 0x079:
            return self.doException(merror.IllegalValue)
        if self.write_byte_count != self.write_count * 2:
            return self.doException(merror.IllegalValue)
        if not context.validate(
            self.function_code, self.write_address, self.write_count
        ):
            return self.doException(merror.IllegalAddress)
        if not context.validate(self.function_code, self.read_address, self.read_count):
            return self.doException(merror.IllegalAddress)
        await context.async_setValues(
            self.function_code, self.write_address, self.write_registers
        )
        registers = await context.async_getValues(
            self.function_code, self.read_address, self.read_count
        )
        if isinstance(registers, ExceptionResponse):
            return registers
        return ReadWriteMultipleRegistersResponse(registers)

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Byte Count(1 byte) + 2 * Quantity of Coils (n Bytes)
        :return:
        """
        return 1 + 1 + 2 * self.read_count

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        params = (
            self.read_address,
            self.read_count,
            self.write_address,
            self.write_count,
        )
        return (
            "ReadWriteNRegisterRequest R(%d,%d) W(%d,%d)"  # pylint: disable=consider-using-f-string
            % params
        )


class ReadWriteMultipleRegistersResponse(ReadHoldingRegistersResponse):
    """Read/write multiple registers.

    The normal response contains the data from the group of registers that
    were read. The byte count field specifies the quantity of bytes to
    follow in the read data field.

    The requested registers can be found in the .registers list.
    """

    function_code = 23
