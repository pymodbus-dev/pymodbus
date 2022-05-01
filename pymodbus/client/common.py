'''
Modbus Client Common
----------------------------------

This is a common client mixin that can be used by
both the synchronous and asynchronous clients to
simplify the interface.
'''
from pymodbus.bit_read_message import *
from pymodbus.bit_write_message import *
from pymodbus.register_read_message import *
from pymodbus.register_write_message import *
from pymodbus.diag_message import *
from pymodbus.file_message import *
from pymodbus.other_message import *

from pymodbus.utilities import ModbusTransactionState


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
    state = ModbusTransactionState.IDLE
    last_frame_end = 0
    silent_interval = 0

    def read_coils(self, address, count=1, **kwargs):
        '''

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadCoilsRequest(address, count, **kwargs)
        return self.execute(request)

    def read_discrete_inputs(self, address, count=1, **kwargs):
        '''

        :param address: The starting address to read from
        :param count: The number of discretes to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadDiscreteInputsRequest(address, count, **kwargs)
        return self.execute(request)

    def write_coil(self, address, value, **kwargs):
        '''

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = WriteSingleCoilRequest(address, value, **kwargs)
        return self.execute(request)

    def write_coils(self, address, values, **kwargs):
        '''

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = WriteMultipleCoilsRequest(address, values, **kwargs)
        return self.execute(request)

    def write_register(self, address, value, **kwargs):
        '''

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = WriteSingleRegisterRequest(address, value, **kwargs)
        return self.execute(request)

    def write_registers(self, address, values, **kwargs):
        '''

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = WriteMultipleRegistersRequest(address, values, **kwargs)
        return self.execute(request)

    def read_holding_registers(self, address, count=1, **kwargs):
        '''

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadHoldingRegistersRequest(address, count, **kwargs)
        return self.execute(request)

    def read_input_registers(self, address, count=1, **kwargs):
        '''

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadInputRegistersRequest(address, count, **kwargs)
        return self.execute(request)

    def readwrite_registers(self, *args, **kwargs):
        '''

        :param read_address: The address to start reading from
        :param read_count: The number of registers to read from address
        :param write_address: The address to start writing to
        :param write_registers: The registers to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadWriteMultipleRegistersRequest(*args, **kwargs)
        return self.execute(request)

    def mask_write_register(self, *args, **kwargs):
        '''

        :param address: The address of the register to write
        :param and_mask: The and bitmask to apply to the register address
        :param or_mask: The or bitmask to apply to the register address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = MaskWriteRegisterRequest(*args, **kwargs)
        return self.execute(request)

#---------------------------------------------------------------------------#
# Exported symbols
#---------------------------------------------------------------------------#
__all__ = [ 'ModbusClientMixin' ]
