'''
Pymodbus Interfaces
---------------------

A collection of base classes that are used throughout
the pymodbus library.
'''
from pymodbus.mexceptions import NotImplementedException

#---------------------------------------------------------------------------#
# Generic
#---------------------------------------------------------------------------#
class Singleton(object):
    '''
    Singleton base class
    http://mail.python.org/pipermail/python-list/2007-July/450681.html
    '''
    def __new__(cls, *args, **kwargs):
        ''' Create a new instance
        '''
        if '_inst' not in vars(cls):
            cls._inst = object.__new__(cls, *args, **kwargs)
        return cls._inst

class Borg(object):
    '''
    Borg base class
    http://code.activestate.com/recipes/66531/
    '''
    __shared_state = {}

    def __init__(self):
        ''' Initialize the new instance
        Make sure this __init__ is called in the child class
        '''
        self.__dict__ = self.__shared_state

#---------------------------------------------------------------------------#
# Project Specific
#---------------------------------------------------------------------------#
class IModbusDecoder(object):
    ''' Modbus Decoder Base Class

    This interface must be implemented by a modbus message
    decoder factory. These factories are responsible for
    abstracting away converting a raw packet into a request / response
    message object.
    '''

    def decode(self, message):
        ''' Wrapper to decode a given packet

        :param message: The raw modbus request packet
        :return: The decoded modbus message or None if error
        '''
        raise NotImplementedException("Method not implemented by derived class")

class IModbusFramer(object):
    '''
    A framer strategy interface. The idea is that we abstract away all the
    detail about how to detect if a current message frame exists, decoding it,
    sending it, etc so that we can plug in a new Framer object (tcp, rtu, ascii)
    '''

    def checkFrame(self):
        ''' Check and decode the next frame

        :returns: True if we successful, False otherwise
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def advanceFrame(self):
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def addToFrame(self, message):
        ''' Add the next message to the frame buffer

        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def isFrameReady(self):
        ''' Check if we should continue decode logic

        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def getFrame(self):
        ''' Get the next frame from the buffer

        :returns: The frame data or ''
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def populateResult(self, result):
        ''' Populates the modbus result with current frame header

        We basically copy the data back over from the current header
        to the result header. This may not be needed for serial messages.

        :param result: The response packet
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def processIncomingPacket(self, data, callback):
        ''' The new packet processing pattern

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        '''
        raise NotImplementedException("Method not implemented by derived class")

    def buildPacket(self, message):
        ''' Creates a ready to send modbus packet

        The raw packet is built off of a fully populated modbus
        request / response message.

        :param message: The request/response to send
        :returns: The built packet
        '''
        raise NotImplementedException("Method not implemented by derived class")

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    'Singleton', 'Borg',
    'IModbusDecoder', 'IModbusFramer',
]
