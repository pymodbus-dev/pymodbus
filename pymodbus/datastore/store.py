"""Modbus Server Datastore.

For each server, you will create a ModbusServerContext and pass
in the default address space for each data access.  The class
will create and manage the data.

Further modification of said data accesses should be performed
with [get,set][access]Values(address, count)

Datastore Implementation
-------------------------

There are two ways that the server datastore can be implemented.
The first is a complete range from "address" start to "count"
number of indices.  This can be thought of as a straight array::

    data = range(1, 1 + count)
    [1,2,3,...,count]

The other way that the datastore can be implemented (and how
many devices implement it) is a associate-array::

    data = {1:"1", 3:"3", ..., count:"count"}
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
will simply not implemented the registers thus causing a single read
or a range read to fail.

I have both methods implemented, and leave it up to the user to change
based on their preference.
"""
# pylint: disable=missing-type-doc
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pymodbus.constants import ExcCodes


# ---------------------------------------------------------------------------#
#  Datablock Storage
# ---------------------------------------------------------------------------#

V = TypeVar('V', list, dict[int, Any])
class BaseModbusDataBlock(ABC, Generic[V]):
    """Base class for a modbus datastore.

    Derived classes must create the following fields:
            @address The starting address point
            @defult_value The default value of the datastore
            @values The actual datastore values

    Derived classes must implemented the following methods:
            getValues(self, address, count=1)
            setValues(self, address, values)
            reset(self)

    Derived classes can implemented the following async methods:
            async_getValues(self, address, count=1)
            async_setValues(self, address, values)
    but are not needed since these standard call the sync. methods.
    """

    values: V
    address: int
    default_value: Any

    async def async_getValues(self, address: int, count=1) -> list[int] | list[bool] | ExcCodes:
        """Return the requested values from the datastore.

        :param address: The starting address
        :param count: The number of values to retrieve
        :raises TypeError:
        """
        return self.getValues(address, count)

    @abstractmethod
    def getValues(self, address:int, count=1) -> list[int] | list[bool] | ExcCodes:
        """Return the requested values from the datastore.

        :param address: The starting address
        :param count: The number of values to retrieve
        :raises TypeError:
        """

    async def async_setValues(self, address: int, values: list[int] | list[bool]) -> None | ExcCodes:
        """Set the requested values in the datastore.

        :param address: The starting address
        :param values: The values to store
        :raises TypeError:
        """
        return self.setValues(address, values)


    @abstractmethod
    def setValues(self, address:int, values) -> None | ExcCodes:
        """Set the requested values in the datastore.

        :param address: The starting address
        :param values: The values to store
        :raises TypeError:
        """

    def reset(self):
        """Reset the datastore to the initialized default value."""

    def __str__(self):
        """Build a representation of the datastore.

        :returns: A string representation of the datastore
        """
        return f"DataStore({len(self.values)}, {self.default_value})"

    def __iter__(self):
        """Iterate over the data block data.

        :returns: An iterator of the data block data
        """
        if isinstance(self.values, dict):
            return iter(self.values.items())
        return enumerate(self.values, self.address)
