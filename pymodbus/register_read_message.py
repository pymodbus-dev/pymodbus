'''
Register Reading Request/Response
---------------------------------
'''

import struct
from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.pdu import ModbusExceptions as merror

class ReadRegistersRequestBase(ModbusRequest):
    '''
    Base class for reading a modbus register
    '''

    def __init__(self, address, count):
        ''' Initializes a new instance

        :param address: The address to start the read from
        :param count: The number of registers to read
        '''
        ModbusRequest.__init__(self)
        self.address = address
        self.count = count

    def encode(self):
        ''' Encodes the request packet

        :return: The encoded packet
        '''
        return struct.pack('>HH', self.address, self.count)

    def decode(self, data):
        ''' Decode a register request packet

        :param data: The request to decode
        '''
        self.address, self.count = struct.unpack('>HH', data)

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadRegisterRequest (%d,%d)" % (self.address, self.count)

class ReadRegistersResponseBase(ModbusResponse):
    '''
    Base class for responsing to a modbus register read
    '''

    def __init__(self, values):
        ''' Initializes a new instance

        :param values: The values to write to
        '''
        ModbusResponse.__init__(self)
        self.registers = values if values != None else []

    def encode(self):
        ''' Encodes the response packet

        :returns: The encoded packet
        '''
        result = chr(len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack('>H', register)
        return result

    def decode(self, data):
        ''' Decode a register response packet

        :param data: The request to decode
        '''
        byte_count = ord(data[0])
        self.registers = []
        for i in range(1, byte_count + 1, 2):
            self.registers.append(struct.unpack('>H', data[i:i+2])[0])

    def getRegValue(self, index):
        ''' Get the requested register

        :param index: The indexed register to retrieve
        :returns: The request register
        '''
        return self.registers[index]

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadRegisterResponse ", self.registers


class ReadHoldingRegistersRequest(ReadRegistersRequestBase):
    '''
    This function code is used to read the contents of a contiguous block
    of holding registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore registers numbered
    1-16 are addressed as 0-15.
    '''
    function_code = 3

    def __init__(self, address=None, count=None):
        ''' Initializes a new instance of the request

        :param address: The starting address to read from
        :param count: The number of registers to read from address
        '''
        ReadRegistersRequestBase.__init__(self, address, count)

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

    def __init__(self, values=None):
        ''' Initializes a new response instance

        :param values: The resulting register values
        '''
        ReadRegistersResponseBase.__init__(self, values)

class ReadInputRegistersRequest(ReadRegistersRequestBase):
    '''
    This function code is used to read from 1 to approx. 125 contiguous
    input registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore input registers
    numbered 1-16 are addressed as 0-15.
    '''
    function_code = 4

    def __init__(self, address=None, count=None):
        ''' Initializes a new instance of the request

        :param address: The starting address to read from
        :param count: The number of registers to read from address
        '''
        ReadRegistersRequestBase.__init__(self, address, count)

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

    def __init__(self, values=None):
        ''' Initializes a new response instance

        :param values: The resulting register values
        '''
        ReadRegistersResponseBase.__init__(self, values)

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

    def __init__(self, raddress=None, rcount=None, waddress=None, wcount=None):
        ''' Initializes a new request message

        :param raddress: The address to start reading from
        :param rcount: The number of registers to read from address
        :param waddress: The address to start writing to
        :param wcount: The number of registers to write from address
        '''
        ModbusRequest.__init__(self)
        self.raddress = raddress
        self.rcount   = rcount
        self.waddress = waddress
        self.wbyte_count = 0
        if wcount != None and wcount > 0:
            self.wregisters = [0] * wcount
        else: self.wregisters = []

    def encode(self):
        ''' Encodes the request packet

        :returns: The encoded packet
        '''
        wcount = len(self.wregisters)
        result = struct.pack('>HHHHB',
                self.raddress, self.rcount, \
                self.waddress, wcount, \
                wcount*2)
        for register in self.wregisters:
            result += struct.pack('>H', register)
        return result

    def decode(self, data):
        ''' Decode the register request packet

        :param data: The request to decode
        '''
        self.raddress, self.rcount, \
        self.waddress, wcount, \
        self.wbyte_count = struct.unpack('>HHHHB', data[:9])
        self.wregisters = []
        for i in range(9, self.wbyte_count+9, 2):
            self.wregisters.append(struct.unpack('>H', data[i:i+2])[0])

    def execute(self, context):
        ''' Run a write single register request against a datastore

        :param context: The datastore to request from
        :returns: An initialized response, exception message otherwise
        '''
        wcount = len(self.wregisters)
        if not (1 <= self.rcount <= 0x07d):
            return self.doException(merror.IllegalValue)
        if not (1 <= wcount <= 0x079):
            return self.doException(merror.IllegalValue)
        if (self.wbyte_count != wcount * 2):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.waddress, wcount):
            return self.doException(merror.IllegalAddress)
        if not context.validate(self.function_code, self.raddress, self.rcount):
            return self.doException(merror.IllegalAddress)
        context.setValues(self.function_code, self.waddress, self.wregisters)
        rvalues = context.getValues(self.function_code, self.raddress, self.rcount)
        return ReadWriteMultipleRegistersResponse(rvalues)

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadWriteNRegisterRequest R(%d,%d) W(%d,%d)" % (self.raddress,
                self.rcount, self.waddress, self.wcount)

class ReadWriteMultipleRegistersResponse(ModbusResponse):
    '''
    The normal response contains the data from the group of registers that
    were read. The byte count field specifies the quantity of bytes to
    follow in the read data field.
    '''
    function_code = 23

    def __init__(self, values=None):
        ''' Initializes a new instance

        :param values: The register values to write
        '''
        ModbusResponse.__init__(self)
        self.registers = values if values != None else []

    def encode(self):
        ''' Encodes the response packet

        :returns: The encoded packet
        '''
        result = chr(len(self.registers)*2)
        for register in self.registers:
            result += struct.pack('>H', register)
        return result

    def decode(self, data):
        ''' Decode the register response packet

        :param data: The response to decode
        '''
        bytes = ord(data[0])
        for i in range(1, bytes, 2):
            self.registers.append(struct.unpack('>H', data[i:i+2])[0])

    def __str__(self):
        ''' Returns a string representation of the instance

        :returns: A string representation of the instance
        '''
        return "ReadWriteNRegisterResponse", self.registers

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ReadHoldingRegistersRequest", "ReadHoldingRegistersResponse",
    "ReadInputRegistersRequest", "ReadInputRegistersResponse",
    "ReadWriteMultipleRegistersRequest", "ReadWriteMultipleRegistersResponse",
]
