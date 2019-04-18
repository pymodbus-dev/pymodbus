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
from pymodbus.exceptions import NotImplementedException, ParameterException
from pymodbus.compat import iteritems, iterkeys, itervalues, get_next

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)


#---------------------------------------------------------------------------#
# Datablock Storage
#---------------------------------------------------------------------------#
class BaseModbusDataBlock(object):
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

    def default(self, count, value=False):
        ''' Used to initialize a store to one value

        :param count: The number of fields to set
        :param value: The default value to set to the fields
        '''
        self.default_value = value
        self.values = [self.default_value] * count
        self.address = 0x00

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
        return "DataStore(%d, %d)" % (len(self.values), self.default_value)

    def __iter__(self):
        ''' Iterater over the data block data

        :returns: An iterator of the data block data
        '''
        if isinstance(self.values, dict):
            return iteritems(self.values)
        return enumerate(self.values, self.address)


class ModbusSequentialDataBlock(BaseModbusDataBlock):
    ''' Creates a sequential modbus datastore '''

    def __init__(self, address, values):
        ''' Initializes the datastore

        :param address: The starting address of the datastore
        :param values: Either a list or a dictionary of values
        '''
        self.address = address
        if hasattr(values, '__iter__'):
            self.values = list(values)
        else:
            self.values = [values]
        self.default_value = self.values[0].__class__()

    @classmethod
    def create(klass):
        ''' Factory method to create a datastore with the
        full address space initialized to 0x00

        :returns: An initialized datastore
        '''
        return klass(0x00, [0x00] * 65536)

    def validate(self, address, count=1):
        ''' Checks to see if the request is in range

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        '''
        result  = (self.address <= address)
        result &= ((self.address + len(self.values)) >= (address + count))
        return result

    def getValues(self, address, count=1):
        ''' Returns the requested values of the datastore

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        start = address - self.address
        return self.values[start:start + count]

    def setValues(self, address, values):
        ''' Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        '''
        if not isinstance(values, list):
            values = [values]
        start = address - self.address
        self.values[start:start + len(values)] = values


class ModbusSparseDataBlock(BaseModbusDataBlock):
    ''' Creates a sparse modbus datastore '''

    def __init__(self, values):
        ''' Initializes the datastore

        Using the input values we create the default
        datastore value and the starting address

        :param values: Either a list or a dictionary of values
        '''
        if isinstance(values, dict):
            self.values = values
        elif hasattr(values, '__iter__'):
            self.values = dict(enumerate(values))
        else: raise ParameterException(
            "Values for datastore must be a list or dictionary")
        self.default_value = get_next(itervalues(self.values)).__class__()
        self.address = get_next(iterkeys(self.values))

    @classmethod
    def create(klass):
        ''' Factory method to create a datastore with the
        full address space initialized to 0x00

        :returns: An initialized datastore
        '''
        return klass([0x00] * 65536)

    def validate(self, address, count=1):
        ''' Checks to see if the request is in range

        :param address: The starting address
        :param count: The number of values to test for
        :returns: True if the request in within range, False otherwise
        '''
        if count == 0:
            return False
        handle = set(range(address, address + count))
        return handle.issubset(set(iterkeys(self.values)))

    def getValues(self, address, count=1):
        ''' Returns the requested values of the datastore

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        return [self.values[i] for i in range(address, address + count)]

    def setValues(self, address, values):
        ''' Sets the requested values of the datastore

        :param address: The starting address
        :param values: The new values to be set
        '''
        if isinstance(values, dict):
            for idx, val in iteritems(values):
                self.values[idx] = val
        else:
            if not isinstance(values, list):
                values = [values]
            for idx, val in enumerate(values):
                self.values[address + idx] = val
