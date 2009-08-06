'''
Pymodbus Interfaces
---------------------

A collection of base classes that are used throughout
the pymodbus library.
'''
from zope.interface import Interface, Attribute

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
# Specific
#---------------------------------------------------------------------------#
class IModbusFramer(Interface):
    '''
    A framer strategy interface. The idea is that we abstract away all the
    detail about how to detect if a current message frame exists, decoding it,
    sending it, etc so that we can plug in a new Framer object (tcp, rtu, ascii)
    '''

    def checkFrame():
        ''' Check and decode the next frame
        @return True if we successful, False otherwise
        '''

    def advanceFrame():
        ''' Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        '''

    def addToFrame(message):
        ''' Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.
        @param message The most recent packet
        '''

    def isFrameReady():
        ''' Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.
        @return True if ready, False otherwise
        '''

    def getFrame():
        ''' Get the next frame from the buffer
        @return The frame data or ''
        '''

    def populateResult(result):
        ''' Populates the modbus result with current frame header
        We basically copy the data back over from the current header
        to the result header. This may not be needed for serial messages.
        @param result The response packet
        '''

    def buildPacket(message):
        ''' Creates a ready to send modbus packet
        Built off of a  modbus request/response
        @param message The request/response to send
        @return The built packet
        '''

__all__ = ['Singleton', 'IModbusFramer']
