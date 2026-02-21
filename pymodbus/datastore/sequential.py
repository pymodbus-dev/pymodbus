"""Modbus Sequential Datastore."""
# pylint: disable=missing-type-doc
from __future__ import annotations

from ..constants import ExcCodes
from .store import BaseModbusDataBlock


class ModbusSequentialDataBlock(BaseModbusDataBlock[list]):
    """Creates a sequential modbus datastore."""

    def __init__(self, address, values):
        """Initialize the datastore.

        :param address: The starting address of the datastore
        :param values: Either a list or a dictionary of values
        """
        self.address = address
        if hasattr(values, "__iter__"):
            self.values = list(values)
        else:
            self.values = [values]

    async def async_getValues(self, address, count=1) -> list[int] | list[bool] | ExcCodes:
        """Return the requested values of the datastore.

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        start = address - self.address
        if start < 0 or len(self.values) < start+count:
            return ExcCodes.ILLEGAL_ADDRESS
        return self.values[start : start + count]

    async def async_setValues(self, address, values) -> None | ExcCodes:
        """Set the requested values of the datastore.

        :param address: The starting address
        :param values: The new values to be set
        """
        if not isinstance(values, list):
            values = [values]
        start = address - self.address
        if start < 0 or len(self.values) < start+len(values):
            return ExcCodes.ILLEGAL_ADDRESS
        self.values[start : start + len(values)] = values
        return None

