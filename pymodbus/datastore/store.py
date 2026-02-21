"""Modbus Server Datastore."""
# pylint: disable=missing-type-doc
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from ..constants import ExcCodes


# ---------------------------------------------------------------------------#
#  Datablock Storage
# ---------------------------------------------------------------------------#

V = TypeVar('V', list, dict[int, Any])
class BaseModbusDataBlock(ABC, Generic[V]):
    """Base class for a modbus datastore."""

    values: V
    address: int
    default_value: Any

    @abstractmethod
    async def async_getValues(self, address: int, count=1) -> list[int] | list[bool] | ExcCodes:
        """Return the requested values from the datastore.

        :param address: The starting address
        :param count: The number of values to retrieve
        :raises TypeError:
        """

    @abstractmethod
    async def async_setValues(self, address: int, values: list[int] | list[bool]) -> None | ExcCodes:
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
