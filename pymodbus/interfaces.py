"""Pymodbus Interfaces.

A collection of base classes that are used throughout
the pymodbus library.
"""
# pylint: disable=missing-type-doc
from pymodbus.exceptions import NotImplementedException


TEXT_METHOD = "Method not implemented by derived class"

# --------------------------------------------------------------------------- #
# Generic
# --------------------------------------------------------------------------- #


class Singleton:  # pylint: disable=too-few-public-methods
    """Singleton base class.

    https://mail.python.org/pipermail/python-list/2007-July/450681.html
    """

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """Create a new instance."""
        if "_inst" not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst


# --------------------------------------------------------------------------- #
# Project Specific
# --------------------------------------------------------------------------- #
class IModbusDecoder:
    """Modbus Decoder Base Class.

    This interface must be implemented by a modbus message
    decoder factory. These factories are responsible for
    abstracting away converting a raw packet into a request / response
    message object.
    """

    def decode(self, message):
        """Decode a given packet.

        :param message: The raw modbus request packet
        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)

    def lookupPduClass(self, function_code):  # pylint: disable=invalid-name
        """Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)

    def register(self, function):
        """Register a function and sub function class with the decoder.

        :param function: Custom function class to register
        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)


class IModbusFramer:
    """A framer strategy interface.

    The idea is that we abstract away all the
    detail about how to detect if a current message frame exists, decoding
    it, sending it, etc so that we can plug in a new Framer object (tcp,
    rtu, ascii).
    """

    def checkFrame(self):  # pylint: disable=invalid-name
        """Check and decode the next frame.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)

    def advanceFrame(self):  # pylint: disable=invalid-name
        """Skip over the current framed message.

        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        raise NotImplementedException(TEXT_METHOD)

    def addToFrame(self, message):  # pylint: disable=invalid-name
        """Add the next message to the frame buffer.

        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)

    def isFrameReady(self):  # pylint: disable=invalid-name
        """Check if we should continue decode logic.

        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)

    def getFrame(self):  # pylint: disable=invalid-name
        """Get the next frame from the buffer.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)

    def populateResult(self, result):  # pylint: disable=invalid-name
        """Populate the modbus result with current frame header.

        We basically copy the data back over from the current header
        to the result header. This may not be needed for serial messages.

        :param result: The response packet
        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)

    def processIncomingPacket(self, data, callback):  # pylint: disable=invalid-name
        """Process new packet pattern.

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)

    def buildPacket(self, message):  # pylint: disable=invalid-name
        """Create a ready to send modbus packet.

        The raw packet is built off of a fully populated modbus
        request / response message.

        :param message: The request/response to send
        :raises NotImplementedException:
        """
        raise NotImplementedException(TEXT_METHOD)


class IModbusSlaveContext:
    """Interface for a modbus slave data context.

    Derived classes must implemented the following methods:
            reset(self)
            validate(self, fx, address, count=1)
            getValues(self, fx, address, count=1)
            setValues(self, fx, address, values)
    """

    __fx_mapper = {2: "d", 4: "i"}
    __fx_mapper.update([(i, "h") for i in (3, 6, 16, 22, 23)])
    __fx_mapper.update([(i, "c") for i in (1, 5, 15)])

    def decode(self, fx):  # pylint: disable=invalid-name
        """Convert the function code to the datastore to.

        :param fx: The function we are working with
        :returns: one of [d(iscretes),i(nputs),h(olding),c(oils)
        """
        return self.__fx_mapper[fx]

    def reset(self):
        """Reset all the datastores to their default values."""
        raise NotImplementedException("Context Reset")

    def validate(self, fx, address, count=1):  # pylint: disable=invalid-name
        """Validate the request to make sure it is in range.

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :raises NotImplementedException:
        """
        raise NotImplementedException("validate context values")

    def getValues(self, fx, address, count=1):  # pylint: disable=invalid-name
        """Get `count` values from datastore.

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :raises NotImplementedException:
        """
        raise NotImplementedException("get context values")

    def setValues(self, fx, address, values):  # pylint: disable=invalid-name
        """Set the datastore with the supplied values.

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        :raises NotImplementedException:
        """
        raise NotImplementedException("set context values")


class IPayloadBuilder:  # pylint: disable=too-few-public-methods
    """This is an interface to a class that can build a payload for a modbus register write command.

    It should abstract the codec for encoding data to the required format
    (bcd, binary, char, etc).
    """

    def build(self):
        """Return the payload buffer as a list.

        This list is two bytes per element and can
        thus be treated as a list of registers.

        :raises NotImplementedException:
        """
        raise NotImplementedException("set context values")


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    "Singleton",
    "IModbusDecoder",
    "IModbusFramer",
    "IModbusSlaveContext",
    "IPayloadBuilder",
]
