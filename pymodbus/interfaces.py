"""
Pymodbus Interfaces
---------------------

A collection of base classes that are used throughout
the pymodbus library.
"""
from pymodbus.exceptions import (NotImplementedException,
                                 MessageRegisterException)


# --------------------------------------------------------------------------- #
# Generic
# --------------------------------------------------------------------------- #
class Singleton(object):
    """
    Singleton base class
    http://mail.python.org/pipermail/python-list/2007-July/450681.html
    """
    def __new__(cls, *args, **kwargs):
        """ Create a new instance
        """
        if '_inst' not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst


# --------------------------------------------------------------------------- #
# Project Specific
# --------------------------------------------------------------------------- #
class IModbusDecoder(object):
    """ Modbus Decoder Base Class

    This interface must be implemented by a modbus message
    decoder factory. These factories are responsible for
    abstracting away converting a raw packet into a request / response
    message object.
    """

    def decode(self, message):
        """ Wrapper to decode a given packet

        :param message: The raw modbus request packet
        :return: The decoded modbus message or None if error
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def lookupPduClass(self, function_code):
        """ Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def register(self, function=None):
        """
        Registers a function and sub function class with the decoder
        :param function: Custom function class to register
        :return:
        """
        raise NotImplementedException(
            "Method not implemented by derived class")


class IModbusFramer(object):
    """
    A framer strategy interface. The idea is that we abstract away all the
    detail about how to detect if a current message frame exists, decoding
    it, sending it, etc so that we can plug in a new Framer object (tcp,
    rtu, ascii).
    """

    def checkFrame(self):
        """ Check and decode the next frame

        :returns: True if we successful, False otherwise
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def advanceFrame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def addToFrame(self, message):
        """ Add the next message to the frame buffer

        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def isFrameReady(self):
        """ Check if we should continue decode logic

        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def getFrame(self):
        """ Get the next frame from the buffer

        :returns: The frame data or ''
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def populateResult(self, result):
        """ Populates the modbus result with current frame header

        We basically copy the data back over from the current header
        to the result header. This may not be needed for serial messages.

        :param result: The response packet
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def processIncomingPacket(self, data, callback):
        """ The new packet processing pattern

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        """
        raise NotImplementedException(
            "Method not implemented by derived class")

    def buildPacket(self, message):
        """ Creates a ready to send modbus packet

        The raw packet is built off of a fully populated modbus
        request / response message.

        :param message: The request/response to send
        :returns: The built packet
        """
        raise NotImplementedException(
            "Method not implemented by derived class")


class IModbusSlaveContext(object):
    """
    Interface for a modbus slave data context

    Derived classes must implemented the following methods:
            reset(self)
            validate(self, fx, address, count=1)
            getValues(self, fx, address, count=1)
            setValues(self, fx, address, values)
    """
    __fx_mapper = {2: 'd', 4: 'i'}
    __fx_mapper.update([(i, 'h') for i in [3, 6, 16, 22, 23]])
    __fx_mapper.update([(i, 'c') for i in [1, 5, 15]])

    def decode(self, fx):
        """ Converts the function code to the datastore to

        :param fx: The function we are working with
        :returns: one of [d(iscretes),i(nputs),h(olding),c(oils)
        """
        return self.__fx_mapper[fx]

    def reset(self):
        """ Resets all the datastores to their default values
        """
        raise NotImplementedException("Context Reset")

    def validate(self, fx, address, count=1):
        """ Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        raise NotImplementedException("validate context values")

    def getValues(self, fx, address, count=1):
        """ Get `count` values from datastore

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        raise NotImplementedException("get context values")

    def setValues(self, fx, address, values):
        """ Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        raise NotImplementedException("set context values")


class IPayloadBuilder(object):
    """
    This is an interface to a class that can build a payload
    for a modbus register write command. It should abstract
    the codec for encoding data to the required format
    (bcd, binary, char, etc).
    """

    def build(self):
        """ Return the payload buffer as a list

        This list is two bytes per element and can
        thus be treated as a list of registers.

        :returns: The payload buffer as a list
        """
        raise NotImplementedException("set context values")


# --------------------------------------------------------------------------- #
# Exported symbols
# --------------------------------------------------------------------------- #
__all__ = [
    'Singleton',
    'IModbusDecoder', 'IModbusFramer', 'IModbusSlaveContext',
    'IPayloadBuilder',
]
