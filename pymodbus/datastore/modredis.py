import redis
from pymodbus.exceptions import NotImplementedException, ParameterException
from pymodbus.interfaces import IModbusSlaveContext
from pymodbus.utilities import pack_bitstring, unpack_bitstring

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
        self.prefix = kwargs.get('prefix', 'pymodbus')
        self.client = redis.Redis(host=host, port=port)
        self.__build_mapping()

    def __str__(self):
        ''' Returns a string representation of the context

        :returns: A string representation of the context
        '''
        return "Redis Slave Context %s" % self.client

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
        return self.__val_callbacks[self.decode(fx)](address, count)

    def getValues(self, fx, address, count=1):
        ''' Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("getValues[%d] %d:%d" % (fx, address, count))
        return self.__get_callbacks[self.decode(fx)](address, count)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        address = address + 1 # section 4.4 of specification
        _logger.debug("setValues[%d] %d:%d" % (fx, address,len(values)))
        self.__set_callbacks[self.decode(fx)](address, values)

    #--------------------------------------------------------------------------#
    # Redis Helper Methods
    #--------------------------------------------------------------------------#
    def __get_prefix(self, key):
        ''' This is a helper to abstract getting bit values

        :param key: The key prefix to use
        :returns: The key prefix to redis
        '''
        return "%s:%s" % (self.prefix, key)

    def __build_mapping(self):
        '''
        A quick helper method to build the function
        code mapper.
        '''
        self.__val_callbacks = {
            'd' : lambda o,c: self.__val_bit('d', o, c),
            'c' : lambda o,c: self.__val_bit('c', o, c),
            'h' : lambda o,c: self.__val_reg('h', o, c),
            'i' : lambda o,c: self.__val_reg('i', o, c),
        }
        self.__get_callbacks = {
            'd' : lambda o,c: self.__get_bit('d', o, c),
            'c' : lambda o,c: self.__get_bit('c', o, c),
            'h' : lambda o,c: self.__get_reg('h', o, c),
            'i' : lambda o,c: self.__get_reg('i', o, c),
        }
        self.__set_callbacks = {
            'd' : lambda o,v: self.__set_bit('d', o, v),
            'c' : lambda o,v: self.__set_bit('c', o, v),
            'h' : lambda o,v: self.__set_reg('h', o, v),
            'i' : lambda o,v: self.__set_reg('i', o, v),
        }

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
        key = self.__get_prefix(key)
        s = divmod(offset, self.__bit_size)[0]
        e = divmod(offset+count, self.__bit_size)[0]

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
        result = unpack_bitstring(result)
        return result[offset:offset+count]

    def __set_bit(self, key, offset, values):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param values: The values to set
        '''
        count = len(values)
        s = divmod(offset, self.__bit_size)[0]
        e = divmod(offset+count, self.__bit_size)[0]
        value = pack_bitstring(values)

        current = self.__get_bit_values(key, offset, count)
        current = (r or self.__bit_default for r in current)
        current = ''.join(current)
        current = current[0:offset] + value + current[offset+count:]
        final   = (current[s:s+self.__bit_size] for s in range(0, count, self.__bit_size))

        key = self.__get_prefix(key)
        request = ('%s:%s' % (key, v) for v in range(s, e+1))
        request = dict(zip(request, final))
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
        key = self.__get_prefix(key)
        #s = divmod(offset, self.__reg_size)[0]
        #e = divmod(offset+count, self.__reg_size)[0]

        #request  = ('%s:%s' % (key, v) for v in range(s, e+1))
        request  = ('%s:%s' % (key, v) for v in range(offset, count+1))
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
        response = [r or self.__reg_default for r in response]
        return response[offset:offset+count]

    def __set_reg(self, key, offset, values):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param values: The values to set
        '''
        count = len(values)
        #s = divmod(offset, self.__reg_size)
        #e = divmod(offset+count, self.__reg_size)

        #current = self.__get_reg_values(key, offset, count)

        key = self.__get_prefix(key)
        request = ('%s:%s' % (key, v) for v in range(offset, count+1))
        request = dict(zip(request, values))
        self.client.mset(request)

