"""Contains base classes for modbus request/response/error packets."""
# pylint: disable=missing-type-doc
import struct

from pymodbus.constants import Defaults
from pymodbus.exceptions import NotImplementedException
from pymodbus.interfaces import Singleton
from pymodbus.logging import Log
from pymodbus.utilities import rtuFrameSize


# --------------------------------------------------------------------------- #
# Base PDUs
# --------------------------------------------------------------------------- #
class ModbusPDU:
    """Base class for all Modbus messages.

    .. attribute:: transaction_id

       This value is used to uniquely identify a request
       response pair.  It can be implemented as a simple counter

    .. attribute:: protocol_id

       This is a constant set at 0 to indicate Modbus.  It is
       put here for ease of expansion.

    .. attribute:: unit

       This is used to route the request to the correct child. In
       the TCP modbus, it is used for routing (or not used at all. However,
       for the serial versions, it is used to specify which child to perform
       the requests against. The value 0x00 represents the broadcast address
       (also 0xff).

    .. attribute:: check

       This is used for LRC/CRC in the serial modbus protocols

    .. attribute:: skip_encode

       This is used when the message payload has already been encoded.
       Generally this will occur when the PayloadBuilder is being used
       to create a complicated message. By setting this to True, the
       request will pass the currently encoded message through instead
       of encoding it again.
    """

    def __init__(self, unit=Defaults.Slave, **kwargs):
        """Initialize the base data for a modbus request.

        :param unit: Modbus slave unit ID

        """
        self.transaction_id = kwargs.get("transaction", Defaults.TransactionId)
        self.protocol_id = kwargs.get("protocol", Defaults.ProtocolId)
        self.unit_id = unit
        self.skip_encode = kwargs.get("skip_encode", False)
        self.check = 0x0000

    def encode(self):
        """Encode the message.

        :raises: A not implemented exception
        """
        raise NotImplementedException()

    def decode(self, data):
        """Decode data part of the message.

        :param data: is a string object
        :raises NotImplementedException:
        """
        raise NotImplementedException()

    @classmethod
    def calculateRtuFrameSize(cls, buffer):  # pylint: disable=invalid-name
        """Calculate the size of a PDU.

        :param buffer: A buffer containing the data that have been received.
        :returns: The number of bytes in the PDU.
        :raises NotImplementedException:
        """
        if hasattr(cls, "_rtu_frame_size"):
            return cls._rtu_frame_size
        if hasattr(cls, "_rtu_byte_count_pos"):
            return rtuFrameSize(buffer, cls._rtu_byte_count_pos)
        raise NotImplementedException(
            f"Cannot determine RTU frame size for {cls.__name__}"
        )


class ModbusRequest(ModbusPDU):
    """Base class for a modbus request PDU."""

    function_code = -1

    def __init__(self, unit=Defaults.Slave, **kwargs):
        """Proxy to the lower level initializer.

        :param unit: Modbus slave unit ID
        """
        super().__init__(unit, **kwargs)

    def doException(self, exception):  # pylint: disable=invalid-name
        """Build an error response based on the function.

        :param exception: The exception to return
        :raises: An exception response
        """
        exc = ExceptionResponse(self.function_code, exception)
        Log.error("Exception response {}", exc)
        return exc


class ModbusResponse(ModbusPDU):
    """Base class for a modbus response PDU.

    .. attribute:: should_respond

       A flag that indicates if this response returns a result back
       to the client issuing the request

    .. attribute:: _rtu_frame_size

       Indicates the size of the modbus rtu response used for
       calculating how much to read.
    """

    should_respond = True

    def __init__(self, unit=Defaults.Slave, **kwargs):
        """Proxy the lower level initializer.

        :param unit: Modbus slave unit ID

        """
        super().__init__(unit, **kwargs)

    def isError(self):  # pylint: disable=invalid-name
        """Check if the error is a success or failure."""
        return self.function_code > 0x80  # pylint: disable=no-member


# --------------------------------------------------------------------------- #
# Exception PDUs
# --------------------------------------------------------------------------- #
class ModbusExceptions(Singleton):  # pylint: disable=too-few-public-methods
    """An enumeration of the valid modbus exceptions."""

    IllegalFunction = 0x01
    IllegalAddress = 0x02
    IllegalValue = 0x03
    SlaveFailure = 0x04
    Acknowledge = 0x05
    SlaveBusy = 0x06
    MemoryParityError = 0x08
    GatewayPathUnavailable = 0x0A
    GatewayNoResponse = 0x0B

    @classmethod
    def decode(cls, code):
        """Give an error code, translate it to a string error name.

        :param code: The code number to translate
        """
        values = {
            v: k
            for k, v in iter(cls.__dict__.items())
            if not k.startswith("__") and not callable(v)
        }
        return values.get(code, None)


class ExceptionResponse(ModbusResponse):
    """Base class for a modbus exception PDU."""

    ExceptionOffset = 0x80
    _rtu_frame_size = 5

    def __init__(self, function_code, exception_code=None, **kwargs):
        """Initialize the modbus exception response.

        :param function_code: The function to build an exception response for
        :param exception_code: The specific modbus exception to return
        """
        super().__init__(**kwargs)
        self.original_code = function_code
        self.function_code = function_code | self.ExceptionOffset
        self.exception_code = exception_code

    def encode(self):
        """Encode a modbus exception response.

        :returns: The encoded exception packet
        """
        return struct.pack(">B", self.exception_code)

    def decode(self, data):
        """Decode a modbus exception response.

        :param data: The packet data to decode
        """
        self.exception_code = int(data[0])

    def __str__(self):
        """Build a representation of an exception response.

        :returns: The string representation of an exception response
        """
        message = ModbusExceptions.decode(self.exception_code)
        parameters = (self.function_code, self.original_code, message)
        return (
            "Exception Response(%d, %d, %s)"  # pylint: disable=consider-using-f-string
            % parameters
        )


class IllegalFunctionRequest(ModbusRequest):
    """Define the Modbus slave exception type "Illegal Function".

    This exception code is returned if the slave::

        - does not implement the function code **or**
        - is not in a state that allows it to process the function
    """

    ErrorCode = 1

    def __init__(self, function_code, **kwargs):
        """Initialize a IllegalFunctionRequest.

        :param function_code: The function we are erroring on
        """
        super().__init__(**kwargs)
        self.function_code = function_code

    def decode(self, data):
        """Decode so this failure will run correctly.

        :param data: Not used
        """

    def execute(self, context):  # pylint: disable=unused-argument
        """Build an illegal function request error response.

        :param context: The current context for the message
        :returns: The error response packet
        """
        return ExceptionResponse(self.function_code, self.ErrorCode)


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #


__all__ = [
    "ModbusRequest",
    "ModbusResponse",
    "ModbusExceptions",
    "ExceptionResponse",
    "IllegalFunctionRequest",
]
