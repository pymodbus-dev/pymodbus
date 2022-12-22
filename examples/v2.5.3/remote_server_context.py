# pylint: disable=missing-type-doc,missing-param-doc,differing-param-doc,missing-raises-doc
"""Although there is a remote server context already in the main library,

it works under the assumption that users would have a server context
of the following form::

    server_context = {
        0x00: client("host1.something.com"),
        0x01: client("host2.something.com"),
        0x02: client("host3.something.com")
    }

This example is how to create a server context where the client is
pointing to the same host, but the requested slave id is used as the
slave for the client::

    server_context = {
        0x00: client("host1.something.com", 0x00),
        0x01: client("host1.something.com", 0x01),
        0x02: client("host1.something.com", 0x02)
    }
"""
import logging

from pymodbus.exceptions import NotImplementedException
from pymodbus.interfaces import IModbusSlaveContext


# -------------------------------------------------------------------------- #
# Logging
# -------------------------------------------------------------------------- #
_logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------- #
# Slave Context
# -------------------------------------------------------------------------- #
# Basically we create a new slave context for the given slave identifier so
# that this slave context will only make requests to that slave with the
# client that the server is maintaining.
# -------------------------------------------------------------------------- #


class RemoteSingleSlaveContext(IModbusSlaveContext):
    """This is a remote server context,

    that allows one to create a server context backed by a single client that
    may be attached to many slave units. This can be used to
    effectively create a modbus forwarding server.
    """

    def __init__(self, context, unit_id):
        """Initialize the datastores

        :param context: The underlying context to operate with
        :param unit_id: The slave that this context will contact
        """
        self.context = context
        self.unit_id = unit_id

    def reset(self):
        """Reset all the datastores to their default values"""
        raise NotImplementedException()

    def validate(self, fx, address, count=1):
        """Validate the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        txt = f"validate[{fx}] {address}:{count}"
        _logger.debug(txt)
        result = self.context.get_callbacks[self.decode(fx)](
            address, count, self.unit_id
        )
        return not result.isError()

    def getValues(self, fx, address, count=1):
        """Get `count` values from datastore

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        txt = f"get values[{fx}] {address}:{count}"
        _logger.debug(txt)
        result = self.context.get_callbacks[self.decode(fx)](
            address, count, self.unit_id
        )
        return self.__extract_result(self.decode(fx), result)

    def setValues(self, fx, address, values):
        """Set the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        txt = f"set values[{fx}] {address}:{len(values)}"
        _logger.debug(txt)
        self.context.set_callbacks[self.decode(fx)](address, values, self.unit_id)

    def __str__(self):
        """Return a string representation of the context

        :returns: A string representation of the context
        """
        return f"Remote Single Slave Context({self.unit_id})"

    def __extract_result(self, f_code, result):
        """Extract the values out of a response.

        The future api should make the result consistent so we can just call `result.getValues()`.

        :param fx: The function to call
        :param result: The resulting data
        """
        if not result.isError():
            if f_code in {"d", "c"}:
                return result.bits
            if f_code in {"h", "i"}:
                return result.registers
            return None
        return result


# -------------------------------------------------------------------------- #
# Server Context
# -------------------------------------------------------------------------- #
# Think of this as simply a dictionary of { unit_id: client(req, unit_id) }
# -------------------------------------------------------------------------- #


class RemoteServerContext:
    """This is a remote server context,

    that allows one to create a server context backed by a single client that
    may be attached to many slave units. This can be used to
    effectively create a modbus forwarding server.
    """

    def __init__(self, client):
        """Initialize the datastores

        :param client: The client to retrieve values with
        """
        self.get_callbacks = {
            "d": lambda a, c, s: client.read_discrete_inputs(  # pylint: disable=unnecessary-lambda
                a, c, s
            ),
            "c": lambda a, c, s: client.read_coils(  # pylint: disable=unnecessary-lambda
                a, c, s
            ),
            "h": lambda a, c, s: client.read_holding_registers(  # pylint: disable=unnecessary-lambda
                a, c, s
            ),
            "i": lambda a, c, s: client.read_input_registers(  # pylint: disable=unnecessary-lambda
                a, c, s
            ),
        }
        self.set_callbacks = {
            "d": lambda a, v, s: client.write_coils(  # pylint: disable=unnecessary-lambda
                a, v, s
            ),
            "c": lambda a, v, s: client.write_coils(  # pylint: disable=unnecessary-lambda
                a, v, s
            ),
            "h": lambda a, v, s: client.write_registers(  # pylint: disable=unnecessary-lambda
                a, v, s
            ),
            "i": lambda a, v, s: client.write_registers(  # pylint: disable=unnecessary-lambda
                a, v, s
            ),
        }
        self._client = client
        self.slaves = {}  # simply a cache

    def __str__(self):
        """Return a string representation of the context

        :returns: A string representation of the context
        """
        return f"Remote Server Context{self._client}"

    def __iter__(self):
        """Iterate over the current collection of slave contexts.

        :returns: An iterator over the slave contexts
        """
        # note, this may not include all slaves
        return iter(self.slaves.items())

    def __contains__(self, slave):
        """Check if the given slave is in this list

        :param slave: slave The slave to check for existence
        :returns: True if the slave exists, False otherwise
        """
        # we don't want to check the cache here as the
        # slave may not exist yet or may not exist any
        # more. The best thing to do is try and fail.
        return True

    def __setitem__(self, slave, context):
        """Use to set a new slave context

        :param slave: The slave context to set
        :param context: The new context to set for this slave
        """
        raise NotImplementedException()  # doesn't make sense here

    def __delitem__(self, slave):
        """Use to access the slave context

        :param slave: The slave context to remove
        """
        raise NotImplementedException()  # doesn't make sense here

    def __getitem__(self, slave):
        """Use to get access to a slave context

        :param slave: The slave context to get
        :returns: The requested slave context
        """
        if slave not in self.slaves:
            self.slaves[slave] = RemoteSingleSlaveContext(self, slave)
        return self.slaves[slave]
