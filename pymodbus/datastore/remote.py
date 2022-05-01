from pymodbus.exceptions import NotImplementedException
from pymodbus.interfaces import IModbusSlaveContext

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
_logger = logging.getLogger(__name__)


#---------------------------------------------------------------------------#
# Context
#---------------------------------------------------------------------------#
class RemoteSlaveContext(IModbusSlaveContext):
    ''' TODO
    This creates a modbus data model that connects to
    a remote device (depending on the client used)
    '''

    def __init__(self, client, unit=None):
        ''' Initializes the datastores

        :param client: The client to retrieve values with
        :param unit: Unit ID of the remote slave
        '''
        self._client = client
        self.unit = unit
        self.__build_mapping()

    def reset(self):
        ''' Resets all the datastores to their default values '''
        raise NotImplementedException()

    def validate(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        '''
        _logger.debug("validate[%d] %d:%d" % (fx, address, count))
        result = self.__get_callbacks[self.decode(fx)](address, count)
        return not result.isError()

    def getValues(self, fx, address, count=1):
        ''' Get `count` values from datastore

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        # TODO deal with deferreds
        _logger.debug("get values[%d] %d:%d" % (fx, address, count))
        result = self.__get_callbacks[self.decode(fx)](address, count)
        return self.__extract_result(self.decode(fx), result)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        # TODO deal with deferreds
        _logger.debug("set values[%d] %d:%d" % (fx, address, len(values)))
        self.__set_callbacks[self.decode(fx)](address, values)

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
        kwargs = {}
        if self.unit:
            kwargs["unit"] = self.unit
        self.__get_callbacks = {
            'd': lambda a, c: self._client.read_discrete_inputs(a, c, **kwargs),
            'c': lambda a, c: self._client.read_coils(a, c, **kwargs),
            'h': lambda a, c: self._client.read_holding_registers(a, c, **kwargs),
            'i': lambda a, c: self._client.read_input_registers(a, c, **kwargs),
        }
        self.__set_callbacks = {
            'd': lambda a, v: self._client.write_coils(a, v, **kwargs),
            'c': lambda a, v: self._client.write_coils(a, v, **kwargs),
            'h': lambda a, v: self._client.write_registers(a, v, **kwargs),
            'i': lambda a, v: self._client.write_registers(a, v, **kwargs),
        }

    def __extract_result(self, fx, result):
        ''' A helper method to extract the values out of
        a response.  TODO make this consistent (values?)
        '''
        if not result.isError():
            if fx in ['d', 'c']:
                return result.bits
            if fx in ['h', 'i']:
                return result.registers
        else:
            return result
