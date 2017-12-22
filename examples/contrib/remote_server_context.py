"""
Although there is a remote server context already in the main library,
it works under the assumption that users would have a server context
of the following form::

    server_context = {
        0x00: client('host1.something.com'),
        0x01: client('host2.something.com'),
        0x02: client('host3.something.com')
    }

This example is how to create a server context where the client is
pointing to the same host, but the requested slave id is used as the
slave for the client::

    server_context = {
        0x00: client('host1.something.com', 0x00),
        0x01: client('host1.something.com', 0x01),
        0x02: client('host1.something.com', 0x02)
    }
"""
from pymodbus.exceptions import NotImplementedException
from pymodbus.interfaces import IModbusSlaveContext

# -------------------------------------------------------------------------- #
# Logging
# -------------------------------------------------------------------------- #

import logging
_logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------- #
# Slave Context
# -------------------------------------------------------------------------- #
# Basically we create a new slave context for the given slave identifier so
# that this slave context will only make requests to that slave with the
# client that the server is maintaining.
# -------------------------------------------------------------------------- #


class RemoteSingleSlaveContext(IModbusSlaveContext):
    """ This is a remote server context that allows one
    to create a server context backed by a single client that
    may be attached to many slave units. This can be used to
    effectively create a modbus forwarding server.
    """

    def __init__(self, context, unit_id):
        """ Initializes the datastores

        :param context: The underlying context to operate with
        :param unit_id: The slave that this context will contact
        """
        self.context = context
        self.unit_id = unit_id

    def reset(self):
        """ Resets all the datastores to their default values """
        raise NotImplementedException()

    def validate(self, fx, address, count=1):
        """ Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        _logger.debug("validate[%d] %d:%d" % (fx, address, count))
        result = self.context.get_callbacks[self.decode(fx)](address,
                                                             count,
                                                             self.unit_id)
        return result.function_code < 0x80

    def getValues(self, fx, address, count=1):
        """ Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        _logger.debug("get values[%d] %d:%d" % (fx, address, count))
        result = self.context.get_callbacks[self.decode(fx)](address,
                                                             count,
                                                             self.unit_id)
        return self.__extract_result(self.decode(fx), result)

    def setValues(self, fx, address, values):
        """ Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        _logger.debug("set values[%d] %d:%d" % (fx, address, len(values)))
        self.context.set_callbacks[self.decode(fx)](address,
                                                    values,
                                                    self.unit_id)

    def __str__(self):
        """ Returns a string representation of the context

        :returns: A string representation of the context
        """
        return "Remote Single Slave Context(%s)" % self.unit_id

    def __extract_result(self, fx, result):
        """ A helper method to extract the values out of
        a response. The future api should make the result
        consistent so we can just call `result.getValues()`.

        :param fx: The function to call
        :param result: The resulting data
        """
        if result.function_code < 0x80:
            if fx in ['d', 'c']:
                return result.bits
            if fx in ['h', 'i']:
                return result.registers
        else: return result

# -------------------------------------------------------------------------- #
# Server Context
# -------------------------------------------------------------------------- #
# Think of this as simply a dictionary of { unit_id: client(req, unit_id) }
# -------------------------------------------------------------------------- #


class RemoteServerContext(object):
    """ This is a remote server context that allows one
    to create a server context backed by a single client that
    may be attached to many slave units. This can be used to
    effectively create a modbus forwarding server.
    """

    def __init__(self, client):
        """ Initializes the datastores

        :param client: The client to retrieve values with
        """
        self.get_callbacks = {
            'd': lambda a, c, s: client.read_discrete_inputs(a, c, s),
            'c': lambda a, c, s: client.read_coils(a, c, s),
            'h': lambda a, c, s: client.read_holding_registers(a, c, s),
            'i': lambda a, c, s: client.read_input_registers(a, c, s),
        }
        self.set_callbacks = {
            'd': lambda a, v, s: client.write_coils(a, v, s),
            'c': lambda a, v, s: client.write_coils(a, v, s),
            'h': lambda a, v, s: client.write_registers(a, v, s),
            'i': lambda a, v, s: client.write_registers(a, v, s),
        }
        self._client = client
        self.slaves = {} # simply a cache

    def __str__(self):
        """ Returns a string representation of the context

        :returns: A string representation of the context
        """
        return "Remote Server Context(%s)" % self._client

    def __iter__(self):
        """ Iterater over the current collection of slave
        contexts.

        :returns: An iterator over the slave contexts
        """
        # note, this may not include all slaves
        return iter(self.slaves.items())

    def __contains__(self, slave):
        """ Check if the given slave is in this list

        :param slave: slave The slave to check for existance
        :returns: True if the slave exists, False otherwise
        """
        # we don't want to check the cache here as the
        # slave may not exist yet or may not exist any
        # more. The best thing to do is try and fail.
        return True

    def __setitem__(self, slave, context):
        """ Used to set a new slave context

        :param slave: The slave context to set
        :param context: The new context to set for this slave
        """
        raise NotImplementedException() # doesn't make sense here

    def __delitem__(self, slave):
        """ Wrapper used to access the slave context

        :param slave: The slave context to remove
        """
        raise NotImplementedException() # doesn't make sense here

    def __getitem__(self, slave):
        """ Used to get access to a slave context

        :param slave: The slave context to get
        :returns: The requested slave context
        """
        if slave not in self.slaves:
            self.slaves[slave] = RemoteSingleSlaveContext(self, slave)
        return self.slaves[slave]
