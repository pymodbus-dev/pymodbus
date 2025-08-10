"""Modbus Sequential Datastore."""
# pylint: disable=missing-type-doc
from __future__ import annotations

from pymodbus.constants import ExcCodes

from .store import BaseModbusDataBlock


# from pymodbus.pdu.exceptionresponse import ExceptionResponse

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
        self.default_value = self.values[0].__class__()

    @classmethod
    def create(cls):
        """Create a datastore.

        With the full address space initialized to 0x00

        :returns: An initialized datastore
        """
        return cls(0x00, [0x00] * 65536)

    def default(self, count, value=False):
        """Use to initialize a store to one value.

        :param count: The number of fields to set
        :param value: The default value to set to the fields
        """
        self.default_value = value
        self.values = [self.default_value] * count
        self.address = 0x00

    def reset(self):
        """Reset the datastore to the initialized default value."""
        self.values = [self.default_value] * len(self.values)

    def getValues(self, address, count=1) -> list[int] | list[bool] | ExcCodes:
        """Return the requested values of the datastore.

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        start = address - self.address
        if start < 0 or len(self.values) < start+count:
            return ExcCodes.ILLEGAL_ADDRESS
        return self.values[start : start + count]

    def setValues(self, address, values) -> None | ExcCodes:
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

