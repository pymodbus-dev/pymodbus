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
from pymodbus.interfaces import IModbusSlaveContext

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging;
_logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Context
#---------------------------------------------------------------------------#
class DatabaseSlaveContext(IModbusSlaveContext):
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
        self.di = kwargs.get('di', ModbusSequentialDataBlock(0, 0))
        self.co = kwargs.get('co', ModbusSequentialDataBlock(0, 0))
        self.ir = kwargs.get('ir', ModbusSequentialDataBlock(0, 0))
        self.hr = kwargs.get('hr', ModbusSequentialDataBlock(0, 0))
        self.__build_mapping()

    def __build_mapping(self):
        '''
        A quick helper method to build the function
        code mapper.
        '''
        self.__mapping = {2:self.di, 4:self.ir}
        self.__mapping.update([(i, self.hr) for i in [3, 6, 16, 23]])
        self.__mapping.update([(i, self.co) for i in [1, 5, 15]])

    def __str__(self):
        ''' Returns a string representation of the context

        :returns: A string representation of the context
        '''
        return "Modbus Slave Context"

    def reset(self):
        ''' Resets all the datastores to their default values '''
        for datastore in [self.di, self.co, self.ir, self.hr]:
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
        return self.__mapping[fx].validate(address, count)

    def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("getValues[%d] %d:%d" % (fx, address, count))
        return self.__mapping[fx].getValues(address, count)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("setValues[%d] %d:%d" % (fx, address,len(values)))
        self.__mapping[fx].setValues(address, values)

    def __create(self, table="pymodbus"):
        '''
        '''
        self.engine = sqlalchemy.create_engine('sqlite:///pymodbus.db', echo=True)
        self.metadata = sqlalchemy.MetaData(self.engine)
        self.table = sqlalchemy.Table(table, self.metadata,
            sqlalchemy.Column('id', sqltypes.Integer, primary_key=True),
            sqlalchemy.Column('name', sqltypes.String(250)),
            sqlalchemy.Column('value', sqltypes.Text))
        self.table.create(checkfirst=True)
        self.connection = self.engine.connect()
    
    def __get(self, key):
        '''
        '''
        query  = self.table.select(self.table.c.id == key)
        result = self.connection.execute(query)
        return result.fetchone()

    def __set(self, value):
        '''
        '''
        query  = self.table.insert().values(**value)
        result = self.connection.execute(query)
        return result.inserted_primary_key
    
    def __update(self, key, value):
        '''
        '''
        query  = self.table.update()
        query  = query.where(self.table.c.id == key).values(**value)
        result = self.connection.execute(query)
        return result.rowcount == 1

    def __delete(self, key):
        '''
        '''
        query  = self.table.delete().where(self.table.c.id == key)
        result = self.connection.execute(query)
        return result.rowcount == 1

