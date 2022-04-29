import redis
from pymodbus.interfaces import IModbusSlaveContext
from pymodbus.utilities import pack_bitstring, unpack_bitstring

#---------------------------------------------------------------------------#
# Logging
#---------------------------------------------------------------------------#
import logging
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
        self.client = kwargs.get('client', redis.Redis(host=host, port=port))
        self._build_mapping()

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
        address = address + 1  # section 4.4 of specification
        _logger.debug("validate[%d] %d:%d" % (fx, address, count))
        return self._val_callbacks[self.decode(fx)](address, count)

    def getValues(self, fx, address, count=1):
        ''' Get `count` values from datastore

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        '''
        address = address + 1  # section 4.4 of specification
        _logger.debug("getValues[%d] %d:%d" % (fx, address, count))
        return self._get_callbacks[self.decode(fx)](address, count)

    def setValues(self, fx, address, values):
        ''' Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        '''
        address = address + 1  # section 4.4 of specification
        _logger.debug("setValues[%d] %d:%d" % (fx, address, len(values)))
        self._set_callbacks[self.decode(fx)](address, values)

    #--------------------------------------------------------------------------#
    # Redis Helper Methods
    #--------------------------------------------------------------------------#
    def _get_prefix(self, key):
        ''' This is a helper to abstract getting bit values

        :param key: The key prefix to use
        :returns: The key prefix to redis
        '''
        return "%s:%s" % (self.prefix, key)

    def _build_mapping(self):
        '''
        A quick helper method to build the function
        code mapper.
        '''
        self._val_callbacks = {
            'd': lambda o, c: self._val_bit('d', o, c),
            'c': lambda o, c: self._val_bit('c', o, c),
            'h': lambda o, c: self._val_reg('h', o, c),
            'i': lambda o, c: self._val_reg('i', o, c),
        }
        self._get_callbacks = {
            'd': lambda o, c: self._get_bit('d', o, c),
            'c': lambda o, c: self._get_bit('c', o, c),
            'h': lambda o, c: self._get_reg('h', o, c),
            'i': lambda o, c: self._get_reg('i', o, c),
        }
        self._set_callbacks = {
            'd': lambda o, v: self._set_bit('d', o, v),
            'c': lambda o, v: self._set_bit('c', o, v),
            'h': lambda o, v: self._set_reg('h', o, v),
            'i': lambda o, v: self._set_reg('i', o, v),
        }

    #--------------------------------------------------------------------------#
    # Redis discrete implementation
    #--------------------------------------------------------------------------#
    _bit_size = 16
    _bit_default = '\x00' * (_bit_size % 8)

    def _get_bit_values(self, key, offset, count):
        ''' This is a helper to abstract getting bit values

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        key = self._get_prefix(key)
        s = divmod(offset, self._bit_size)[0]
        e = divmod(offset + count, self._bit_size)[0]

        request = ('%s:%s' % (key, v) for v in range(s, e + 1))
        response = self.client.mget(request)
        return response

    def _val_bit(self, key, offset, count):
        ''' Validates that the given range is currently set in redis.
        If any of the keys return None, then it is invalid.

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        response = self._get_bit_values(key, offset, count)
        return True if None not in response else False

    def _get_bit(self, key, offset, count):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        response = self._get_bit_values(key, offset, count)
        response = (r or self._bit_default for r in response)
        result = ''.join(response)
        result = unpack_bitstring(result)
        return result[offset:offset + count]

    def _set_bit(self, key, offset, values):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param values: The values to set
        '''
        count = len(values)
        s = divmod(offset, self._bit_size)[0]
        e = divmod(offset + count, self._bit_size)[0]
        value = pack_bitstring(values)

        current = self._get_bit_values(key, offset, count)
        current = (r or self._bit_default for r in current)
        current = ''.join(current)
        current = current[0:offset] + value.decode('utf-8') + current[offset + count:]
        final = (current[s:s + self._bit_size] for s in range(0, count, self._bit_size))

        key = self._get_prefix(key)
        request = ('%s:%s' % (key, v) for v in range(s, e + 1))
        request = dict(zip(request, final))
        self.client.mset(request)

    #--------------------------------------------------------------------------#
    # Redis register implementation
    #--------------------------------------------------------------------------#
    _reg_size = 16
    _reg_default = '\x00' * (_reg_size % 8)

    def _get_reg_values(self, key, offset, count):
        ''' This is a helper to abstract getting register values

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        key = self._get_prefix(key)
        #s = divmod(offset, self.__reg_size)[0]
        #e = divmod(offset+count, self.__reg_size)[0]

        #request  = ('%s:%s' % (key, v) for v in range(s, e + 1))
        request = ('%s:%s' % (key, v) for v in range(offset, count + 1))
        response = self.client.mget(request)
        return response

    def _val_reg(self, key, offset, count):
        ''' Validates that the given range is currently set in redis.
        If any of the keys return None, then it is invalid.

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        response = self._get_reg_values(key, offset, count)
        return None not in response

    def _get_reg(self, key, offset, count):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param count: The number of bits to read
        '''
        response = self._get_reg_values(key, offset, count)
        response = [r or self._reg_default for r in response]
        return response[offset:offset + count]

    def _set_reg(self, key, offset, values):
        '''

        :param key: The key prefix to use
        :param offset: The address offset to start at
        :param values: The values to set
        '''
        count = len(values)
        #s = divmod(offset, self.__reg_size)
        #e = divmod(offset+count, self.__reg_size)

        #current = self.__get_reg_values(key, offset, count)

        key = self._get_prefix(key)
        request = ('%s:%s' % (key, v) for v in range(offset, count + 1))
        request = dict(zip(request, values))
        self.client.mset(request)
