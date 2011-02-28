'''
Contains base classes for modbus request/response/error packets
'''
from pymodbus.interfaces import Singleton
from pymodbus.exceptions import NotImplementedException
from pymodbus.constants import Defaults
from utilities import rtuFrameSize

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Base PDU's
#---------------------------------------------------------------------------#
class ModbusPDU(object):
    '''
    Base class for all Modbus mesages

    .. attribute:: transaction_id

        This value is used to uniquely identify a request
        response pair.  It can be implemented as a simple counter

    .. attribute:: protocol_id

        This is a constant set at 0 to indicate Modbus.  It is
        put here for ease of expansion.

    .. attribute:: unit_id
    
        This is used to route the request to the correct child. In
        the TCP modbus, it is used for routing (or not used at all.  However, for
        the serial versions, it is used to specify which child to perform the
        requests against. The value 0x00 represents the broadcast address (also 0xff).

    .. attribute:: check
    
        This is used for LRC/CRC in the serial modbus protocols
    '''

    def __init__(self, **kwargs):
        ''' Initializes the base data for a modbus request '''
        self.transaction_id = kwargs.get('transaction', Defaults.TransactionId)
        self.protocol_id = kwargs.get('protocol', Defaults.ProtocolId)
        self.unit_id = kwargs.get('unit', Defaults.UnitId)
        self.check = 0x0000

    def encode(self):
        ''' Encodes the message

        :raises: A not implemented exception
        '''
        raise NotImplementedException()

    def decode(self, data):
        ''' Decodes data part of the message.

        :param data: is a string object
        :raises: A not implemented exception
        '''
        raise NotImplementedException()

    @classmethod
    def calculateRtuFrameSize(cls, buffer):
        ''' Calculates the size of a PDU.

        :param buffer: A buffer containing the data that have been received.
        :returns: The number of bytes in the PDU.
        '''
        if hasattr(cls, '_rtu_frame_size'):
            return cls._rtu_frame_size
        elif hasattr(cls, '_rtu_byte_count_pos'):
            return rtuFrameSize(buffer, cls._rtu_byte_count_pos)
        else: raise NotImplementedException(
            "Cannot determine RTU frame size for %s" % cls.__name__)

class ModbusRequest(ModbusPDU):
    ''' Base class for a modbus request PDU '''

    def __init__(self, **kwargs):
        ''' Proxy to the lower level initializer '''
        ModbusPDU.__init__(self, **kwargs)

    def doException(self, exception):
        ''' Builds an error response based on the function

        :param exception: The exception to return
        :raises: An exception response
        '''
        _logger.error("Exception Response F(%d) E(%d)" %
                (self.function_code, exception))
        return ExceptionResponse(self.function_code, exception)

class ModbusResponse(ModbusPDU):
    ''' Base class for a modbus response PDU '''

    def __init__(self, **kwargs):
        ''' Proxy to the lower level initializer '''
        ModbusPDU.__init__(self, **kwargs)

#---------------------------------------------------------------------------#
# Exception PDU's
#---------------------------------------------------------------------------#
class ModbusExceptions(Singleton):
    '''
    An enumeration of the valid modbus exceptions
    '''
    IllegalFunction         = 0x01
    IllegalAddress          = 0x02
    IllegalValue            = 0x03
    SlaveFailure            = 0x04
    Acknowledge             = 0x05
    SlaveBusy               = 0x06
    MemoryParityError       = 0x08
    GatewayPathUnavailable  = 0x0A
    GatewayNoResponse       = 0x0B

class ExceptionResponse(ModbusResponse):
    ''' Base class for a modbus exception PDU '''
    ExceptionOffset = 0x80
    _rtu_frame_size = 5

    def __init__(self, function_code, exception_code=None, **kwargs):
        ''' Initializes the modbus exception response

        :param function_code: The function to build an exception response for
        :param exception_code: The specific modbus exception to return
        '''
        ModbusResponse.__init__(self, **kwargs)
        self.function_code = function_code | self.ExceptionOffset
        self.exception_code = exception_code

    def encode(self):
        ''' Encodes a modbus exception response

        :returns: The encoded exception packet
        '''
        return chr(self.exception_code)

    def decode(self, data):
        ''' Decodes a modbus exception response

        :param data: The packet data to decode
        '''
        self.exception_code = ord(data[0])

    def __str__(self):
        ''' Builds a representation of an exception response

        :returns: The string representation of an exception response
        '''
        return "Exception Response (%d, %d)" % (self.function_code,
                self.exception_code)

class IllegalFunctionRequest(ModbusRequest):
    '''
    Defines the Modbus slave exception type 'Illegal Function'
    This exception code is returned if the slave::

        - does not implement the function code **or**
        - is not in a state that allows it to process the function
    '''
    ErrorCode = 1

    def __init__(self, function_code, **kwargs):
        ''' Initializes a IllegalFunctionRequest

        :param function_code: The function we are erroring on
        '''
        ModbusRequest.__init__(self, **kwargs)
        self.function_code = function_code

    def decode(self, data):
        ''' This is here so this failure will run correctly

        :param data: Not used
        '''
        pass

    def execute(self, context):
        ''' Builds an illegal function request error response

        :param context: The current context for the message
        :returns: The error response packet
        '''
        return ExceptionResponse(self.function_code, self.ErrorCode)

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    'ModbusRequest', 'ModbusResponse', 'ModbusExceptions',
    'ExceptionResponse', 'IllegalFunctionRequest',
]
