'''
Custom exceptions to be used in the Modbus code
'''

class ModbusException(Exception):
    ''' Base modbus exception '''

    def __init__(self, string):
        self.string = string

    def __str__(self):
        return 'Modbus Error: %s' % self.string

class ModbusIOException(ModbusException):
    ''' Error resulting from data i/o '''

    def __init__(self, string=""):
        message = "[Input/Output] %s" % string
        ModbusException.__init__(self, message)

class ParameterException(ModbusException):
    ''' Error resulting from invalid paramater '''

    def __init__(self, string=""):
        message = "[Invalid Paramter] %s" % string
        ModbusException.__init__(self, message)

class NotImplementedException(ModbusException):
    ''' Error resulting from not implemented function '''

    def __init__(self, string=""):
        message = "[Not Implemented] %s" % string
        ModbusException.__init__(self, message)
