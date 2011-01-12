'''
'''
from pymodbus.bit_read_message import *
from pymodbus.bit_write_message import *
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *
from pymodbus.diag_message import *
from pymodbus.file_message import *
from pymodbus.other_message import *

class ModbusClientMixin(object):
    '''
    This is a modbus client mixin that provides additional factory
    methods for all the current modbus methods. This can be used
    instead of the normal pattern of::

       # instead of this
       client = ModbusClient(...)
       request = ReadCoilsRequest(1,10)
       response = client.execute(request)

       # now like this
       client = ModbusClient(...)
       response = client.read_coils(1, 10)
    '''

    def read_coils(self, address, count=1):
        '''

        :returns: A deferred response handle
        '''
        request = ReadCoilsRequest(address, count)
        return self.execute(request)

    def read_discrete_inputs(self, address, count=1):
        '''

        :returns: A deferred response handle
        '''
        request = ReadDiscreteInputsRequest(address, count)
        return self.execute(request)

    def write_coil(self, address, value):
        '''

        :returns: A deferred response handle
        '''
        request = WriteSingleCoilRequest(address, value)
        return self.execute(request)

    def write_coils(self, address, values):
        '''

        :returns: A deferred response handle
        '''
        request = WriteMultipleCoilsRequest(address, values)
        return self.execute(request)

    def write_register(self, address, value):
        '''

        :returns: A deferred response handle
        '''
        request = WriteSingleRegisterRequest(address, value)
        return self.execute(request)

    def write_registers(self, address, values):
        '''

        :returns: A deferred response handle
        '''
        request = WriteMultipleRegistersRequest(address, values)
        return self.execute(request)

    def read_holding_registers(self, address, count=1):
        '''

        :returns: A deferred response handle
        '''
        request = ReadHoldingRegistersRequest(address, count)
        return self.execute(request)

    def read_input_registers(self, address, count=1):
        '''

        :returns: A deferred response handle
        '''
        request = ReadInputRegistersRequest(address, count)
        return self.execute(request)

    def readwrite_registers(self, *arguments):
        '''

        :returns: A deferred response handle
        '''
        request = ReadWriteMultipleRegistersRequest(*arguments)
        return self.execute(request)


