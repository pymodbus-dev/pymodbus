"""Context for datastore."""
import logging

from pymodbus.exceptions import NoSuchSlaveException
from pymodbus.interfaces import IModbusSlaveContext
from pymodbus.datastore.store import ModbusSequentialDataBlock
from pymodbus.constants import Defaults

# ---------------------------------------------------------------------------#
#  Logging
# ---------------------------------------------------------------------------#
_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------#
#  Slave Contexts
# ---------------------------------------------------------------------------#
class ModbusSlaveContext(IModbusSlaveContext):
    """This creates a modbus data model with each data access stored in a block."""

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        """Initialize the datastores.

        Defaults to fully populated
        sequential data blocks if none are passed in.

        :param kwargs: Each element is a ModbusDataBlock

            "di" - Discrete Inputs initializer
            "co" - Coils initializer
            "hr" - Holding Register initializer
            "ir" - Input Registers iniatializer
        """
        self.store = {}
        self.store["d"] = kwargs.get("di", ModbusSequentialDataBlock.create())
        self.store["c"] = kwargs.get("co", ModbusSequentialDataBlock.create())
        self.store["i"] = kwargs.get("ir", ModbusSequentialDataBlock.create())
        self.store["h"] = kwargs.get("hr", ModbusSequentialDataBlock.create())
        self.zero_mode = kwargs.get("zero_mode", Defaults.ZeroMode)

    def __str__(self):
        """Return a string representation of the context.

        :returns: A string representation of the context
        """
        return "Modbus Slave Context"

    def reset(self):
        """Reset all the datastores to their default values."""
        for datastore in iter(self.store.values()):
            datastore.reset()

    def validate(self, fc_as_hex, address, count=1):
        """Validate the request to make sure it is in range.

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        if not self.zero_mode:
            address = address + 1
        txt = f"validate: fc-[{fc_as_hex}] address-{address}: count-{count}"
        _logger.debug(txt)
        return self.store[self.decode(fc_as_hex)].validate(address, count)

    def getValues(self, fc_as_hex, address, count=1):
        """Get `count` values from datastore.

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        if not self.zero_mode:
            address = address + 1
        txt = f"getValues: fc-[{fc_as_hex}] address-{address}: count-{count}"
        _logger.debug(txt)
        return self.store[self.decode(fc_as_hex)].getValues(address, count)

    def setValues(self, fc_as_hex, address, values):
        """Set the datastore with the supplied values.

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        if not self.zero_mode:
            address = address + 1
        txt = f"setValues[{fc_as_hex}] address-{address}: count-{len(values)}"
        _logger.debug(txt)
        self.store[self.decode(fc_as_hex)].setValues(address, values)

    def register(self, function_code, fc_as_hex, datablock=None):
        """Register a datablock with the slave context.

        :param fc: function code (int)
        :param fx: string representation of function code (e.g "cf" )
        :param datablock: datablock to associate with this function code
        :return:
        """
        self.store[fc_as_hex] = datablock or ModbusSequentialDataBlock.create()
        self._IModbusSlaveContext__fx_mapper[  # pylint: disable=no-member
            function_code
        ] = fc_as_hex


class ModbusServerContext:
    """This represents a master collection of slave contexts.

    If single is set to true, it will be treated as a single
    context so every unit-id returns the same context. If single
    is set to false, it will be interpreted as a collection of
    slave contexts.
    """

    def __init__(self, slaves=None, single=True):
        """Initialize a new instance of a modbus server context.

        :param slaves: A dictionary of client contexts
        :param single: Set to true to treat this as a single context
        """
        self.single = single
        self._slaves = slaves or {}
        if self.single:
            self._slaves = {Defaults.UnitId: self._slaves}

    def __iter__(self):
        """Iterate over the current collection of slave contexts.

        :returns: An iterator over the slave contexts
        """
        return iter(self._slaves.items())

    def __contains__(self, slave):
        """Check if the given slave is in this list.

        :param slave: slave The slave to check for existence
        :returns: True if the slave exists, False otherwise
        """
        if self.single and self._slaves:
            return True
        return slave in self._slaves

    def __setitem__(self, slave, context):
        """Use to set a new slave context.

        :param slave: The slave context to set
        :param context: The new context to set for this slave
        """
        if self.single:
            slave = Defaults.UnitId
        if 0xF7 >= slave >= 0x00:
            self._slaves[slave] = context
        else:
            raise NoSuchSlaveException(f"slave index :{slave} out of range")

    def __delitem__(self, slave):
        """Use to access the slave context.

        :param slave: The slave context to remove
        """
        if not self.single and (0xF7 >= slave >= 0x00):
            del self._slaves[slave]
        else:
            raise NoSuchSlaveException(f"slave index: {slave} out of range")

    def __getitem__(self, slave):
        """Use to get access to a slave context.

        :param slave: The slave context to get
        :returns: The requested slave context
        """
        if self.single:
            slave = Defaults.UnitId
        if slave in self._slaves:
            return self._slaves.get(slave)
        raise NoSuchSlaveException(
            f"slave - {slave} does not exist, or is out of range"
        )

    def slaves(self):
        """Define slaves."""
        # Python3 now returns keys() as iterable
        return list(self._slaves.keys())
