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
class RemoteSlaveContext(IModbusSlaveContext):
    ''' TODO
    This creates a modbus data model that connects to
    a remote device (depending on the client used)
    '''

    def __init__(self, client):
        ''' Initializes the datastores

        :param client: The client to retrieve values with
        '''
        self._client = client

    def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        # TODO deal with deferreds
        return self.__mapping[fx](address, count)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        # TODO deal with deferreds
        self.__mapping[fx](address, values)

    def __str__(self):
        ''' Returns a string representation of the context

        :returns: A string representation of the context
        '''
        return "Remote Slave Context(%s)" % self._client

    def __build_mapping(self):
        '''
        A quick helper method to build the function
        code mapper.
        '''
        self.__mapping = {2:'d', 4:'i'}
        self.__mapping.update([(i, 'h') for i in [3, 6, 16, 23]])
        self.__mapping.update([(i, 'c') for i in [1, 5, 15]])

        self.__get_callbacks = {
            'd' : lambda a,c: self._client.read_discrete_inputs(a, c),
            'c' : lambda a,c: self._client.read_coils(a, c),
            'h' : lambda a,c: self._client.read_holding_registers(a, c),
            'i' : lambda a,c: self._client.read_input_registers(a, c),
        }
        self.__set_callbacks = {
            'd' : lambda a,v: self._client.write_discrete_inputs(a, v),
            'c' : lambda a,v: self._client.write_coils(a, v),
            'h' : lambda a,v: self._client.read_holding_registers(a, v),
            'i' : lambda a,v: self._client.read_input_registers(a, v),
        }

