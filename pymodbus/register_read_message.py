'''
Register Reading Request/Response
---------------------------------
'''
import struct
from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.pdu import ModbusExceptions as merror

_REG_STRUCT = struct.Struct('>H')
_reg_pack = _REG_STRUCT.pack
_reg_unpack_base = _REG_STRUCT.unpack
def _reg_unpack(raw):
    '''
    Unpack a register in binary form.  Returns the integer value.
    '''
    return _reg_unpack_base(raw)[0]

class ReadRegistersRequestBase(ModbusRequest):
    '''
    Base class for reading a modbus register
    '''
    _rtu_frame_size = 8

    def __init__(self, address, count, **kwargs):
        ''' Initializes a new instance

        :param address: The address to start the read from
        :param count: The number of registers to read
        '''
        ModbusRequest.__init__(self, **kwargs)
        self.address = address
        self.count = count
        frame_struct = struct.Struct('>HH')
        self._unpack = frame_struct.unpack
        self._pack = frame_struct.pack

    def encode(self):
        ''' Encodes the request packet

        :return: The encoded packet
        '''
        return self._pack(self.address, self.count)

    def decode(self, data):
        ''' Decode a register request packet

        :param data: The request to decode
        '''
        self.address, self.count = self._unpack(data)

    def getResponseSize(self):
        ''' Returns expected packet size of response for this request

        :returns: The expected packet size
        '''
        return 1 + 2 * self.count

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadRegisterRequest (%d,%d)" % (self.address, self.count)

class RegisterResponseMixin(object):
    '''
    Partial class that implements lazy-reading of 16-bit integer registers
    from a packet dump.  The object provides two attributes:

    * registers: accepts or returns a list of integers which represent the
                 integer values of the registers.
    * raw_registers: accepts or returns the binary representation of the
                 register block, as it would be sent/received by Modbus.

    Writing to one immediately invalidates the contents of the other (setting
    the internal value to None); if that value is then requested, it will be
    computed on the fly and stored.
    '''

    def __init__(self, values=None, **kwargs):
        self._reg_pack = _reg_pack
        self._reg_unpack = _reg_unpack
        self._registers = None
        self._raw_registers = None
        self._count = 0
        if values is not None:
            self.registers = values

    @property
    def count(self):
        '''
        Return the length of the register block.
        '''
        return self._count

    def _get_registers(self):
        '''
        Read and return the value of the registers as integers.
        '''
        if self._registers is None:
            # Compute the register values
            if self._raw_registers is None:
                return []
            self._registers = [
                    self._reg_unpack(self._raw_registers[baddr:baddr + 2])
                    for baddr in range(0, self._count*2, 2)
            ]
        return self._registers

    def _set_registers(self, values):
        '''
        Set the integer value for the registers.
        '''
        self._registers = list(values)
        self._count = len(values)
        self._raw_registers = None

    registers = property(_get_registers, _set_registers)

    def _get_raw_registers(self):
        '''
        Read and return the value of the registers as integers.
        '''
        if self._raw_registers is None:
            # Compute the register values
            if self._registers is None:
                return ''
            self._raw_registers = ''.join([
                    self._reg_pack(r) for r in self._registers
            ])
        return self._raw_registers

    def _set_raw_registers(self, values):
        '''
        Set the integer value for the registers.
        '''
        self._raw_registers = str(values)
        self._count = len(self._raw_registers)/2
        self._registers = None

    raw_registers = property(_get_raw_registers, _set_raw_registers)


class ReadRegistersResponseBase(ModbusResponse, RegisterResponseMixin):
    '''
    Base class for responsing to a modbus register read
    '''

    _rtu_byte_count_pos = 2

    def __init__(self, values, **kwargs):
        ''' Initializes a new instance

        :param values: The values to write to
        '''
        ModbusResponse.__init__(self, **kwargs)
        RegisterResponseMixin.__init__(self, values)

    def encode(self):
        ''' Encodes the response packet

        :returns: The encoded packet
        '''
        return '%c%s' % (self.count * 2, self.raw_registers)

    def decode(self, data):
        ''' Decode a register response packet

        :param data: The request to decode
        '''
        byte_count = ord(data[0])
        assert byte_count == len(data)-1
        self.raw_registers = data[1:]

    def getRegister(self, index):
        ''' Get the requested register

        :param index: The indexed register to retrieve
        :returns: The request register
        '''
        return self.registers[index]

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadRegisterResponse (%d)" % self.count


class ReadHoldingRegistersRequest(ReadRegistersRequestBase):
    '''
    This function code is used to read the contents of a contiguous block
    of holding registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore registers numbered
    1-16 are addressed as 0-15.
    '''
    function_code = 3

    def __init__(self, address=None, count=None, **kwargs):
        ''' Initializes a new instance of the request

        :param address: The starting address to read from
        :param count: The number of registers to read from address
        '''
        ReadRegistersRequestBase.__init__(self, address, count, **kwargs)

    def execute(self, context):
        ''' Run a read holding request against a datastore

        :param context: The datastore to request from
        :returns: An initialized response, exception message otherwise
        '''
        if not (1 <= self.count <= 0x7d):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = context.getValues(self.function_code, self.address, self.count)
        return ReadHoldingRegistersResponse(values)


class ReadHoldingRegistersResponse(ReadRegistersResponseBase):
    '''
    This function code is used to read the contents of a contiguous block
    of holding registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore registers numbered
    1-16 are addressed as 0-15.
    '''
    function_code = 3

    def __init__(self, values=None, **kwargs):
        ''' Initializes a new response instance

        :param values: The resulting register values
        '''
        ReadRegistersResponseBase.__init__(self, values, **kwargs)


class ReadInputRegistersRequest(ReadRegistersRequestBase):
    '''
    This function code is used to read from 1 to approx. 125 contiguous
    input registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore input registers
    numbered 1-16 are addressed as 0-15.
    '''
    function_code = 4

    def __init__(self, address=None, count=None, **kwargs):
        ''' Initializes a new instance of the request

        :param address: The starting address to read from
        :param count: The number of registers to read from address
        '''
        ReadRegistersRequestBase.__init__(self, address, count, **kwargs)

    def execute(self, context):
        ''' Run a read input request against a datastore

        :param context: The datastore to request from
        :returns: An initialized response, exception message otherwise
        '''
        if not (1 <= self.count <= 0x7d):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = context.getValues(self.function_code, self.address, self.count)
        return ReadInputRegistersResponse(values)


class ReadInputRegistersResponse(ReadRegistersResponseBase):
    '''
    This function code is used to read from 1 to approx. 125 contiguous
    input registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore input registers
    numbered 1-16 are addressed as 0-15.
    '''
    function_code = 4

    def __init__(self, values=None, **kwargs):
        ''' Initializes a new response instance

        :param values: The resulting register values
        '''
        ReadRegistersResponseBase.__init__(self, values, **kwargs)


class ReadWriteMultipleRegistersRequest(ModbusRequest):
    '''
    This function code performs a combination of one read operation and one
    write operation in a single MODBUS transaction. The write
    operation is performed before the read.

    Holding registers are addressed starting at zero. Therefore holding
    registers 1-16 are addressed in the PDU as 0-15.

    The request specifies the starting address and number of holding
    registers to be read as well as the starting address, number of holding
    registers, and the data to be written. The byte count specifies the
    number of bytes to follow in the write data field."
    '''
    function_code = 23
    _rtu_byte_count_pos = 10

    def __init__(self, **kwargs):
        ''' Initializes a new request message

        :param read_address: The address to start reading from
        :param read_count: The number of registers to read from address
        :param write_address: The address to start writing to
        :param write_registers: The registers to write to the specified address
        '''
        ModbusRequest.__init__(self, **kwargs)
        self.read_address    = kwargs.get('read_address', 0x00)
        self.read_count      = kwargs.get('read_count', 0)
        self.write_address   = kwargs.get('write_address', 0x00)
        self.write_registers = kwargs.get('write_registers', None)
        if not hasattr(self.write_registers, '__iter__'):
            self.write_registers = [self.write_registers]
        self.write_count = len(self.write_registers)
        self.write_byte_count = self.write_count * 2

        header_struct = struct.Struct('>HHHHB')
        self._pack_header = header_struct.pack
        self._unpack_header = header_struct.unpack
        self._pack_reg = _reg_pack
        self._unpack_reg = _reg_unpack

    def encode(self):
        ''' Encodes the request packet

        :returns: The encoded packet
        '''
        result = self._pack_header(
                self.read_address,  self.read_count, \
                self.write_address, self.write_count, self.write_byte_count)
        for register in self.write_registers:
            result += self._pack_reg(register)
        return result

    def decode(self, data):
        ''' Decode the register request packet

        :param data: The request to decode
        '''
        self.read_address,  self.read_count,  \
        self.write_address, self.write_count, \
        self.write_byte_count = self._unpack_header(data[:9])
        self.write_registers  = []
        for i in range(9, self.write_byte_count + 9, 2):
            register = self._unpack_reg(data[i:i + 2])
            self.write_registers.append(register)

    def execute(self, context):
        ''' Run a write single register request against a datastore

        :param context: The datastore to request from
        :returns: An initialized response, exception message otherwise
        '''
        if not (1 <= self.read_count <= 0x07d):
            return self.doException(merror.IllegalValue)
        if not (1 <= self.write_count <= 0x079):
            return self.doException(merror.IllegalValue)
        if (self.write_byte_count != self.write_count * 2):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.write_address,
                                self.write_count):
            return self.doException(merror.IllegalAddress)
        if not context.validate(self.function_code, self.read_address,
                                self.read_count):
            return self.doException(merror.IllegalAddress)
        context.setValues(self.function_code, self.write_address,
                          self.write_registers)
        registers = context.getValues(self.function_code, self.read_address,
                                      self.read_count)
        return ReadWriteMultipleRegistersResponse(registers)

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        params = (self.read_address, self.read_count, self.write_address,
                  self.write_count)
        return "ReadWriteNRegisterRequest R(%d,%d) W(%d,%d)" % params


class ReadWriteMultipleRegistersResponse(ModbusResponse, RegisterResponseMixin):
    '''
    The normal response contains the data from the group of registers that
    were read. The byte count field specifies the quantity of bytes to
    follow in the read data field.
    '''
    function_code = 23
    _rtu_byte_count_pos = 2

    def __init__(self, values=None, **kwargs):
        ''' Initializes a new instance

        :param values: The register values to write
        '''
        ModbusResponse.__init__(self, **kwargs)
        RegisterResponseMixin.__init__(self, values)

    def encode(self):
        ''' Encodes the response packet

        :returns: The encoded packet
        '''
        return '%c%s' % (self.count * 2, self.raw_registers)

    def decode(self, data):
        ''' Decode the register response packet

        :param data: The response to decode
        '''
        bytecount = ord(data[0])
        assert bytecount == len(data)-1

        # Seems the test case assumes the old content of 'registers' is
        # something other than empty.  I don't know enough of the code to
        # understand why this is.  So I'll append the new data to preserve
        # the existing behaviour.
        self.raw_registers = '%s%s' % (self.raw_registers, data[1:])

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadWriteNRegisterResponse (%d)" % self.count

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "ReadHoldingRegistersRequest", "ReadHoldingRegistersResponse",
    "ReadInputRegistersRequest", "ReadInputRegistersResponse",
    "ReadWriteMultipleRegistersRequest", "ReadWriteMultipleRegistersResponse",
]
