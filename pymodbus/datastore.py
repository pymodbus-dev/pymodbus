"""
Modbus Server Datastore
-------------------------

For each server, you will create a ModbusServerContext and pass
in the default address space for each data access.  The class
will create and manage the data.

Further modification of said data accesses should be performed
with [get,set][access]Values(address, count)

Datastore Implementation
-------------------------

There are two ways that the server datastore can be implemented.
The first is a complete range from 'address' start to 'count'
number of indecies.  This can be thought of as a straight array::

    data = range(1, 1 + count)
    [1,2,3,...,count]

The other way that the datastore can be implemented (and how
many devices implement it) is a associate-array::

    data = {1:'1', 3:'3', ..., count:'count'}
    [1,3,...,count]

The difference between the two is that the latter will allow
arbitrary gaps in its datastore while the former will not.
This is seen quite commonly in some modbus implementations.
What follows is a clear example from the field:

Say a company makes two devices to monitor power usage on a rack.
One works with three-phase and the other with a single phase. The
company will dictate a modbus data mapping such that registers::

    n:      phase 1 power
    n+1:    phase 2 power
    n+2:    phase 3 power

Using this, layout, the first device will implement n, n+1, and n+2,
however, the second device may set the latter two values to 0 or
will simply not implmented the registers thus causing a single read
or a range read to fail.

I have both methods implemented, and leave it up to the user to change
based on their preference.
"""
from pymodbus.mexceptions import *

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging;
_logger = logging.getLogger("pymodbus.protocol")

#---------------------------------------------------------------------------#
# Datablock Storage
#---------------------------------------------------------------------------#
class ModbusDataBlock(object):
    '''
    Base class for a modbus datastore

    Derived classes must create the following fields:
            @address The starting address point
            @defult_value The default value of the datastore
            @values The actual datastore values

    Derived classes must implemented the following methods:
            validate(self, address, count=1)
            getValues(self, address, count=1)
            setValues(self, address, values)
    '''

    def default(self, count, value):
        ''' Used to initialize a store to one value

        :param count: The number of fields to set
        :param value: The default value to set to the fields
        '''
        self.default_value = value
        self.values = [self.default_value] * count

    def reset(self):
        ''' Resets the datastore to the initialized default value '''
        self.values = [self.default_value] * len(self.values)

    def validate(self, address, count=1):
        ''' Checks to see if the request is in range

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        '''
        raise NotImplementedException("Datastore Address Check")

    def getValues(self, address, count=1):
        ''' Returns the requested values from the datastore

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        raise NotImplementedException("Datastore Value Retrieve")

    def setValues(self, address, values):
        ''' Returns the requested values from the datastore

        :param address: The starting address
        :param values: The values to store
        '''
        raise NotImplementedException("Datastore Value Retrieve")

    def __str__(self):
        ''' Build a representation of the datastore

        :returns: A string representation of the datastore
        '''
        return "DataStore(%d, %d)" % (self.address, self.default_value)

    def __iter__(self):
        ''' Iterater over the data block data

        :returns: An iterator of the data block data
        '''
        if isinstance(dict, self.values):
            return self.values.iteritems()
        return enumerate(self.values)

class ModbusSequentialDataBlock(ModbusDataBlock):
    ''' Creates a sequential modbus datastore '''

    def __init__(self, address, values):
        ''' Initializes the datastore

        :param address: The starting address of the datastore
        :param values: Either a list or a dictionary of values
        '''
        self.address = address
        if isinstance(values, list):
            self.values = values
        else: self.values = [values]
        self.default_value = self.values[0]

    def validate(self, address, count=1):
        ''' Checks to see if the request is in range

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        '''
        if self.address > address:
            return False
        if ((self.address + len(self.values)) <
                (address + count)): return False
        return True

    def getValues(self, address, count=1):
        ''' Returns the requested values of the datastore

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        b = address - self.address
        return self.values[b:b+count]

    def setValues(self, address, values):
        ''' Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        '''
        b = address - self.address
        self.values[b:b+len(values)] = values

class ModbusSparseDataBlock(ModbusDataBlock):
    ''' Creates a sparse modbus datastore '''

    def __init__(self, values):
        ''' Initializes the datastore

        Using the input values we create the default
        datastore value and the starting address

        :param values: Either a list or a dictionary of values
        '''
        if isinstance(values, dict):
            self.values = values
        elif isinstance(values, list):
            self.values = dict([(i,v) for i,v in enumerate(values)])
        else: raise ParameterException(
                        "Values for datastore must be a list or dictionary")
        self.default_value = self.values.values()[0]
        self.address = self.values.iterkeys().next()

    def validate(self, address, count=1):
        ''' Checks to see if the request is in range

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        '''
        return set(range(address, address + count)
                        ).issubset(set(self.values.iterkeys()))

    def getValues(self, address, count=1):
        ''' Returns the requested values of the datastore

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        return [self.values[i]
                for i in range(address, address + count)]

    def setValues(self, address, values):
        ''' Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        '''
        for i,v in enumerate(values):
            self.values[address + i] = v

#---------------------------------------------------------------------------#
# Device Data Control
#---------------------------------------------------------------------------#
class ModbusSlaveContext(object):
    '''
    This creates a modbus data model with each data access
    stored in its own personal block
    '''

    def __init__(self, **kwargs):
        ''' Initializes the datastores
        @param kwargs
                Each element is a ModbusDataBlock
                'd' - Discrete Inputs initializer
                'c' - Coils initializer
                'h' - Holding Register initializer
                'i' - Input Registers iniatializer
        '''
        for k in ['d', 'c', 'h', 'i']:
            if not kwargs.has_key(k):
                kwargs[k] = ModbusSequentialDataBlock(0, 0)
            if not isinstance(kwargs[k], ModbusDataBlock):
                raise ParameterException("Assigned datastore is not a ModbusDataBlock")
        self.di = kwargs['d']
        self.co = kwargs['c']
        self.ir = kwargs['i']
        self.hr = kwargs['h']
        self.__mapping = {
            2:self.di, 3:self.hr, 4:self.ir,
            1:self.co, 5:self.co, 15:self.co,
            6:self.hr, 16:self.hr, 23:self.hr
       }

    def __str__(self):
        ''' Returns a string representation of the context

        :returns: A string representation of the context
        '''
        return "[Slave Context]\n", [self.co, self.di, self.ir, self.hr]

    def reset(self):
        ''' Resets all the datastores to their default values '''
        for i in [self.di, self.co, self.ir, self.hr]:
            i.reset()

    def validate(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        '''
        _logger.debug("validate[%d] %d:%d" % (fx, address, count))
        return self.__mapping[fx].validate(address, count)

    def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        _logger.debug("getValues[%d] %d:%d" % (fx, address, count))
        return self.__mapping[fx].getValues(address, count)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        _logger.debug("setValues[%d] %d:%d" % (fx, address,len(values)))
        self.__mapping[fx].setValues(address, values)

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
        self.__slaves = slaves if slaves != None else {}

    def __iter__(self):
        ''' Iterater over the current collection of slave
        contexts.

        :returns: An iterator over the slave contexts
        '''
        if self.single:
            return {0x00: self.__slaves}.iteritems()
        return self.__slaves.iteritems()

    def __setitem__(self, slave, context):
        ''' Wrapper used to access the slave context

        :param slave: slave The context to set
        :param context: The new context to set for this slave
        '''
        if self.single:
            self.__slaves = context
        else: self.__slaves[slave] = context

    def __getitem__(self, slave):
        ''' Wrapper used to access the slave context

        :param slave: The slave context to get
        :returns: The requested slave context
        '''
        if self.single:
            return self.__slaves
        if self.__slaves.has_key(slave):
            return self.__slaves.get(slave)
        else: raise ParameterException("Slave does not exist")

#---------------------------------------------------------------------------# 
# Exported symbols
#---------------------------------------------------------------------------# 
__all__ = [
    "ModbusSequentialDataBlock", "ModbusSparseDataBlock",
    "ModbusSlaveContext", "ModbusServerContext",
]
