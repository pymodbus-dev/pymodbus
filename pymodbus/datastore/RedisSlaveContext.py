import redis
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
class RedisSlaveContext(IModbusSlaveContext):
    '''
    This is a modbus slave context using redis as a backing
    store.
    '''

    def __init__(self, **kwargs):
        ''' Initializes the datastores

        :param host: The host to connect to
        :param port: The port to connect to
        :param prefix: A prefix for the keys
        '''
        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 6379)
        prefix = kwargs.get('prefix', 'pymodbus')
        self.client = redis.Redis(host=host, port=port)
        self.__build_mapping()

    def __build_mapping(self):
        '''
        A quick helper method to build the function
        code mapper.
        '''
        self.__mapping = {2:'d', 4:'i'}
        self.__mapping.update([(i, 'h') for i in [3, 6, 16, 23]])
        self.__mapping.update([(i, 'c') for i in [1, 5, 15]])

        # sigh, pattern matching would be nice
        self.__val_callbacks = {
            'd' : lambda o,c: self.__val_bits('d', o, c),
            'c' : lambda o,c: self.__val_bits('c', o, c),
            'h' : lambda o,c: self.__val_reg('h', o, c),
            'i' : lambda o,c: self.__val_reg('i', o, c),
        }
        self.__get_callbacks = {
            'd' : lambda o,c: self.__get_bits('d', o, c),
            'c' : lambda o,c: self.__get_bits('c', o, c),
            'h' : lambda o,c: self.__get_reg('h', o, c),
            'i' : lambda o,c: self.__get_reg('i', o, c),
        }
        self.__set_callbacks = {
            'd' : lambda o,v: self.__set_bits('d', o, v),
            'c' : lambda o,v: self.__set_bits('c', o, v),
            'h' : lambda o,v: self.__set_reg('h', o, v),
            'i' : lambda o,v: self.__set_reg('i', o, v),
        }

    def __str__(self):
        ''' Returns a string representation of the context

        :returns: A string representation of the context
        '''
        return "Modbus Slave Context"

    def reset(self):
        ''' Resets all the datastores to their default values '''
        self.client.flushall()

    def validate(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("validate[%d] %d:%d" % (fx, address, count))
        return self.__val_callbacks[self.__mapping[fx]](offset, count)

    def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("getValues[%d] %d:%d" % (fx, address, count))
        return self.__get_callbacks[self.__mapping[fx]](offset, count)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("setValues[%d] %d:%d" % (fx, address,len(values)))
        self.__get_callbacks[self.__mapping[fx]](offset, values)

    #--------------------------------------------------------------------------#
    # Redis discrete implementation
    #--------------------------------------------------------------------------#
    __bit_size    = 16
    __bit_default = '\x00' * (__bit_size % 8)

    def __get_bit_values(self, key, offset, count):
        ''' This is a helper to abstract getting bit values

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        key = self.prefix + key
        s = divmod(offset, self.__bit_size)
        e = divmod(offset+count, self.__bit_size)

        request  = ('%s:%s' % (key, v) for v in range(s, e+1))
        response = self.client.mget(request)
        return response

    def __val_bit(self, key, offset, count):
        ''' Validates that the given range is currently set in redis.
        If any of the keys return None, then it is invalid.

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        response = self.__get_bit_values(key, offset, count)
        return None not in response

    def __get_bit(self, key, offset, count):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        response = self.__get_bit_values(key, offset, count)
        response = (r or self.__bit_default for r in response)
        result = ''.join(response)
        return result[offset, offset+count]

    def __set_bit(self, key, offset, values):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param values: The values to set
        '''
        count = len(values)
        s = divmod(offset, self.__bit_size)
        e = divmod(offset+count, self.__bit_size)

        current = self.__get_bit_values(key, offset, count)

        key = self.prefix + key
        request = ('%s:%s' % (key, v) for v in range(s, e+1))
        request = zip(request, current)
        self.client.mset(request)

    #--------------------------------------------------------------------------#
    # Redis register implementation
    #--------------------------------------------------------------------------#
    __reg_size    = 16
    __reg_default = '\x00' * (__reg_size % 8)

    def __get_reg_values(self, key, offset, count):
        ''' This is a helper to abstract getting register values

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        key = self.prefix + key
        s = divmod(offset, self.__reg_size)
        e = divmod(offset+count, self.__reg_size)

        request  = ('%s:%s' % (key, v) for v in range(s, e+1))
        response = self.client.mget(request)
        return response

    def __val_reg(self, key, offset, count):
        ''' Validates that the given range is currently set in redis.
        If any of the keys return None, then it is invalid.

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        response = self.__get_reg_values(key, offset, count)
        return None not in response

    def __get_reg(self, key, offset, count):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        response = self.__get_reg_values(key, offset, count)
        response = (r or self.__reg_default for r in response)
        result = ''.join(response)
        return result[offset, offset+count]

    def __set_reg(self, key, offset, values):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param values: The values to set
        '''
        count = len(values)
        s = divmod(offset, self.__reg_size)
        e = divmod(offset+count, self.__reg_size)

        current = self.__get_reg_values(key, offset, count)

        key = self.prefix + key
        request = ('%s:%s' % (key, v) for v in range(s, e+1))
        request = zip(request, current)
        self.client.mset(request)

