'''
File Record Read/Write Messages
-------------------------------

Currently none of these messages are implemented
'''

import struct
from pymodbus.pdu import ModbusRequest
from pymodbus.pdu import ModbusResponse
from pymodbus.pdu import ModbusExceptions as merror

#---------------------------------------------------------------------------#
# TODO finish these requests
#---------------------------------------------------------------------------#
# Read File Record 20
# Write File Record 21
# mask write register 22

class ReadFifoQueueRequest(ModbusRequest):
    '''
    This function code allows to read the contents of a First-In-First-Out
    (FIFO) queue of register in a remote device. The function returns a
    count of the registers in the queue, followed by the queued data.
    Up to 32 registers can be read: the count, plus up to 31 queued data registers. 

    The queue count register is returned first, followed by the queued data registers. 
    The function reads the queue contents, but does not clear them.
    '''
    function_code = 0x18

    def __init__(self, address):
        ''' Initializes a new instance

        :param address: The fifo pointer address (0x0000 to 0xffff)
        '''
        ModbusRequest.__init__(self)
        self.address = address

    def execute(self, context):
        ''' Run a read exeception status request against the store

        :param context: The datastore to request from
        :returns: The populated response
        '''
        values = [] # dunno where this should come from
        if len(values) > 31:
            return self.doException(merror.IllegalValue)
        return ReadFifoQueueResponse(values)

class ReadFifoQueueResponse(ModbusResponse):
    '''
    In a normal response, the byte count shows the quantity of bytes to
    follow, including the queue count bytes and value register bytes
    (but not including the error check field).  The queue count is the
    quantity of data registers in the queue (not including the count register). 

    If the queue count exceeds 31, an exception response is returned with an
    error code of 03 (Illegal Data Value).
    '''
    function_code = 0x18

    def __init__(self, values):
        ''' Initializes a new instance

        :param values: The list of values of the fifo to return
        '''
        ModbusRequest.__init__(self)
        self.values = values

    def encode(self):
        ''' Encodes the response

        :returns: The byte encoded message
        '''
        length = len(self.values) * 2
        packet = struct.pack('>HH', 2 + length, length)
        for value in self.values:
            packet += struct.pack('>H', value)

    def decode(self, data):
        ''' Decodes a the response

        :param data: The packet data to decode
        '''
        self.values = []
        length, count = struct.unpack('>HH', data)
        for i in xrange(0, count):
            self.values.append(struct.unpack('>H', data[2 + i * 2]))

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ReadFifoQueueRequest", "ReadFifoQueueResponse",
]
