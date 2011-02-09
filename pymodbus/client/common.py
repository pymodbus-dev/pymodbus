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

    def read_coils(self, address, count=1, unit=0x00):
        '''

        :param address: The starting address to read from
        :param count: The number of coils to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadCoilsRequest(address, count)
        request.unit_id = unit
        return self.execute(request)

    def read_discrete_inputs(self, address, count=1, unit=0x00):
        '''

        :param address: The starting address to read from
        :param count: The number of discretes to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadDiscreteInputsRequest(address, count)
        request.unit_id = unit
        return self.execute(request)

    def write_coil(self, address, value, unit=0x00):
        '''

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = WriteSingleCoilRequest(address, value)
        request.unit_id = unit
        return self.execute(request)

    def write_coils(self, address, values, unit=0x00):
        '''

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = WriteMultipleCoilsRequest(address, values)
        request.unit_id = unit
        return self.execute(request)

    def write_register(self, address, value, unit=0x00):
        '''

        :param address: The starting address to write to
        :param value: The value to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = WriteSingleRegisterRequest(address, value)
        request.unit_id = unit
        return self.execute(request)

    def write_registers(self, address, values, unit=0x00):
        '''

        :param address: The starting address to write to
        :param values: The values to write to the specified address
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = WriteMultipleRegistersRequest(address, values)
        request.unit_id = unit
        return self.execute(request)

    def read_holding_registers(self, address, count=1, unit=0x00):
        '''

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadHoldingRegistersRequest(address, count)
        request.unit_id = unit
        return self.execute(request)

    def read_input_registers(self, address, count=1, unit=0x00):
        '''

        :param address: The starting address to read from
        :param count: The number of registers to read
        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadInputRegistersRequest(address, count)
        request.unit_id = unit
        return self.execute(request)

    def readwrite_registers(self, *args, **kwargs):
        '''

        :param unit: The slave unit this request is targeting
        :returns: A deferred response handle
        '''
        request = ReadWriteMultipleRegistersRequest(*args, **kwargs)
        request.unit_id = kwargs.get('unit', 0x00)
        return self.execute(request)


