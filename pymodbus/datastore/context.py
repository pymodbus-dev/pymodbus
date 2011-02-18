from pymodbus.exceptions import NotImplementedException, ParameterException
from pymodbus.interfaces import IModbusSlaveContext
from pymodbus.datastore.store import ModbusSequentialDataBlock

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging;
_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Slave Contexts
#---------------------------------------------------------------------------#
class ModbusSlaveContext(IModbusSlaveContext):
    '''
    This creates a modbus data model with each data access
    stored in its own personal block
    '''

    def __init__(self, *args, **kwargs):
        ''' Initializes the datastores
        :param kwargs: Each element is a ModbusDataBlock

            'di' - Discrete Inputs initializer
            'co' - Coils initializer
            'hr' - Holding Register initializer
            'ir' - Input Registers iniatializer
        '''
	self.store = {}
        self.store['d'] = kwargs.get('di', ModbusSequentialDataBlock(0, 0))
        self.store['c'] = kwargs.get('co', ModbusSequentialDataBlock(0, 0))
        self.store['i'] = kwargs.get('ir', ModbusSequentialDataBlock(0, 0))
        self.store['h'] = kwargs.get('hr', ModbusSequentialDataBlock(0, 0))

    def __str__(self):
        ''' Returns a string representation of the context

        :returns: A string representation of the context
        '''
        return "Modbus Slave Context"

    def reset(self):
        ''' Resets all the datastores to their default values '''
        for datastore in self.store.values():
            datastore.reset()

    def validate(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("validate[%d] %d:%d" % (fx, address, count))
        return self.store[self.decode(fx)].validate(address, count)

    def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("getValues[%d] %d:%d" % (fx, address, count))
        return self.store[self.decode(fx)].getValues(address, count)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("setValues[%d] %d:%d" % (fx, address,len(values)))
        self.store[self.decode(fx)].setValues(address, values)

class ModbusServerContext(object):
    ''' This represents a master collection of slave contexts.
    If single is set to true, it will be treated as a single
    context so every unit-id returns the same context. If single
    is set to false, it will be interpreted as a collection of
    slave contexts.
    '''

    def __init__(self, slaves=None, single=True):
        ''' Initializes a new instance of a modbus server context.

        :param slaves: A dictionary of client contexts
        :param single: Set to true to treat this as a single context
        '''
        self.single   = single
        self.__slaves = slaves or {}
        if self.single:
            self.__slaves = {0x00: self.__slaves}

    def __iter__(self):
        ''' Iterater over the current collection of slave
        contexts.

        :returns: An iterator over the slave contexts
        '''
        return self.__slaves.iteritems()

    def __setitem__(self, slave, context):
        ''' Wrapper used to access the slave context

        :param slave: slave The context to set
        :param context: The new context to set for this slave
        '''
        if self.single: slave = 0x00
        if 0xf7 >= slave >= 0x00:
            self.__slaves[slave] = context
        else: raise ParameterException('slave index out of range')

    def __getitem__(self, slave):
        ''' Wrapper used to access the slave context

        :param slave: The slave context to get
        :returns: The requested slave context
        '''
        if self.single: slave = 0x00
        if self.__slaves.has_key(slave):
            return self.__slaves.get(slave)
        else: raise ParameterException("slave does not exist, or is out of range")
