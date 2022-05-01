from pymodbus.exceptions import ParameterException, NoSuchSlaveException
from pymodbus.interfaces import IModbusSlaveContext
from pymodbus.datastore.store import ModbusSequentialDataBlock
from pymodbus.constants import Defaults
from pymodbus.compat import iteritems, itervalues

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
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
        ''' Initializes the datastores, defaults to fully populated
        sequential data blocks if none are passed in.

        :param kwargs: Each element is a ModbusDataBlock

            'di' - Discrete Inputs initializer
            'co' - Coils initializer
            'hr' - Holding Register initializer
            'ir' - Input Registers iniatializer
        '''
        self.store = dict()
        self.store['d'] = kwargs.get('di', ModbusSequentialDataBlock.create())
        self.store['c'] = kwargs.get('co', ModbusSequentialDataBlock.create())
        self.store['i'] = kwargs.get('ir', ModbusSequentialDataBlock.create())
        self.store['h'] = kwargs.get('hr', ModbusSequentialDataBlock.create())
        self.zero_mode = kwargs.get('zero_mode', Defaults.ZeroMode)

    def __str__(self):
        ''' Returns a string representation of the context

        :returns: A string representation of the context
        '''
        return "Modbus Slave Context"

    def reset(self):
        ''' Resets all the datastores to their default values '''
        for datastore in itervalues(self.store):
            datastore.reset()

    def validate(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        '''
        if not self.zero_mode:
            address = address + 1
        _logger.debug("validate: fc-[%d] address-%d: count-%d" % (fx, address,
                                                                  count))
        return self.store[self.decode(fx)].validate(address, count)

    def getValues(self, fx, address, count=1):
        ''' Get `count` values from datastore

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        if not self.zero_mode:
            address = address + 1
        _logger.debug("getValues fc-[%d] address-%d: count-%d" % (fx, address,
                                                                  count))
        return self.store[self.decode(fx)].getValues(address, count)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        if not self.zero_mode:
            address = address + 1
        _logger.debug("setValues[%d] %d:%d" % (fx, address, len(values)))
        self.store[self.decode(fx)].setValues(address, values)

    def register(self, fc, fx, datablock=None):
        """
        Registers a datablock with the slave context
        :param fc: function code (int)
        :param fx: string representation of function code (e.g 'cf' )
        :param datablock: datablock to associate with this function code
        :return:
        """
        self.store[fx] = datablock or ModbusSequentialDataBlock.create()
        self._IModbusSlaveContext__fx_mapper[fc] = fx


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
        self.single = single
        self._slaves = slaves or {}
        if self.single:
            self._slaves = {Defaults.UnitId: self._slaves}

    def __iter__(self):
        ''' Iterater over the current collection of slave
        contexts.

        :returns: An iterator over the slave contexts
        '''
        return iteritems(self._slaves)

    def __contains__(self, slave):
        ''' Check if the given slave is in this list

        :param slave: slave The slave to check for existence
        :returns: True if the slave exists, False otherwise
        '''
        if self.single and self._slaves:
            return True
        else:
            return slave in self._slaves

    def __setitem__(self, slave, context):
        ''' Used to set a new slave context

        :param slave: The slave context to set
        :param context: The new context to set for this slave
        '''
        if self.single:
            slave = Defaults.UnitId
        if 0xf7 >= slave >= 0x00:
            self._slaves[slave] = context
        else:
            raise NoSuchSlaveException('slave index :{} '
                                       'out of range'.format(slave))

    def __delitem__(self, slave):
        ''' Wrapper used to access the slave context

        :param slave: The slave context to remove
        '''
        if not self.single and (0xf7 >= slave >= 0x00):
            del self._slaves[slave]
        else:
            raise NoSuchSlaveException('slave index: {} '
                                       'out of range'.format(slave))

    def __getitem__(self, slave):
        ''' Used to get access to a slave context

        :param slave: The slave context to get
        :returns: The requested slave context
        '''
        if self.single:
            slave = Defaults.UnitId
        if slave in self._slaves:
            return self._slaves.get(slave)
        else:
            raise NoSuchSlaveException("slave - {} does not exist, "
                                       "or is out of range".format(slave))

    def slaves(self):
        # Python3 now returns keys() as iterable
        return list(self._slaves.keys())
