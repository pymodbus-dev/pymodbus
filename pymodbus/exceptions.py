'''
Pymodbus Exceptions
--------------------

Custom exceptions to be used in the Modbus code.
'''


class ModbusException(Exception):
    ''' Base modbus exception '''

    def __init__(self, string):
        ''' Initialize the exception
        :param string: The message to append to the error
        '''
        self.string = string

    def __str__(self):
        return 'Modbus Error: %s' % self.string


class ModbusIOException(ModbusException):
    ''' Error resulting from data i/o '''

    def __init__(self, string=""):
        ''' Initialize the exception
        :param string: The message to append to the error
        '''
        message = "[Input/Output] %s" % string
        ModbusException.__init__(self, message)


class ParameterException(ModbusException):
    ''' Error resulting from invalid paramater '''

    def __init__(self, string=""):
        ''' Initialize the exception
        :param string: The message to append to the error
        '''
        message = "[Invalid Paramter] %s" % string
        ModbusException.__init__(self, message)


class NotImplementedException(ModbusException):
    ''' Error resulting from not implemented function '''

    def __init__(self, string=""):
        ''' Initialize the exception
        :param string: The message to append to the error
        '''
        message = "[Not Implemented] %s" % string
        ModbusException.__init__(self, message)


class ConnectionException(ModbusException):
    ''' Error resulting from a bad connection '''

    def __init__(self, string=""):
        ''' Initialize the exception
        :param string: The message to append to the error
        '''
        message = "[Connection] %s" % string
        ModbusException.__init__(self, message)

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [
    "ModbusException", "ModbusIOException",
    "ParameterException", "NotImplementedException",
    "ConnectionException",
]
