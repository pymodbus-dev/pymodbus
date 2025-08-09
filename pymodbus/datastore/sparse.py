"""Modbus Sparse Datastore."""
# pylint: disable=missing-type-doc
from __future__ import annotations

from typing import Any

from pymodbus.constants import ExcCodes
from pymodbus.exceptions import ParameterException

from .store import BaseModbusDataBlock


class ModbusSparseDataBlock(BaseModbusDataBlock[dict[int, Any]]):
    """A sparse modbus datastore.

    E.g Usage.
    sparse = ModbusSparseDataBlock({10: [3, 5, 6, 8], 30: 1, 40: [0]*20})

    This would create a datablock with 3 blocks
    One starts at offset 10 with length 4, one at 30 with length 1, and one at 40 with length 20

    sparse = ModbusSparseDataBlock([10]*100)
    Creates a sparse datablock of length 100 starting at offset 0 and default value of 10

    sparse = ModbusSparseDataBlock() --> Create empty datablock
    sparse.setValues(0, [10]*10)  --> Add block 1 at offset 0 with length 10 (default value 10)
    sparse.setValues(30, [20]*5)  --> Add block 2 at offset 30 with length 5 (default value 20)

    Unless 'mutable' is set to True during initialization, the datablock cannot be altered with
    setValues (new datablocks cannot be added)
    """

    def __init__(self, values=None, mutable=True):
        """Initialize a sparse datastore.

        Will only answer to addresses registered,
        either initially here, or later via setValues()

        :param values: Either a list or a dictionary of values
        :param mutable: Whether the data-block can be altered later with setValues (i.e add more blocks)

        If values is a list, a sequential datablock will be created.

        If values is a dictionary, it should be in {offset: <int | list>} format
        For each list, a sparse datablock is created, starting at 'offset' with the length of the list
        For each integer, the value is set for the corresponding offset.

        """
        self.values = {}
        self._process_values(values)
        self.mutable = mutable
        self.default_value = self.values.copy()

    @classmethod
    def create(cls, values=None):
        """Create sparse datastore.

        Use setValues to initialize registers.

        :param values: Either a list or a dictionary of values
        :returns: An initialized datastore
        """
        return cls(values)

    def reset(self):
        """Reset the store to the initially provided defaults."""
        self.values = self.default_value.copy()

    def getValues(self, address, count=1) -> list[int] | list[bool] | ExcCodes:
        """Return the requested values of the datastore.

        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        try:
            values = [self.values[i] for i in range(address, address + count)]
        except KeyError:
            return ExcCodes.ILLEGAL_ADDRESS
        return values

    def _process_values(self, values):
        """Process values."""

        def _process_as_dict(values):
            for idx, val in iter(values.items()):
                if isinstance(val, (list, tuple)):
                    for i, v_item in enumerate(val):
                        self.values[idx + i] = v_item
                else:
                    self.values[idx] = int(val)

        if isinstance(values, dict):
            _process_as_dict(values)
            return
        if hasattr(values, "__iter__"):
            values = dict(enumerate(values))
        elif values is None:
            values = {}  # Must make a new dict here per instance
        else:
            raise ParameterException(
                "Values for datastore must be a list or dictionary"
            )
        _process_as_dict(values)

    def setValues(self, address, values, use_as_default=False) -> None | ExcCodes:
        """Set the requested values of the datastore.

        :param address: The starting address
        :param values: The new values to be set
        :param use_as_default: Use the values as default
        :raises ParameterException:
        """
        try:
            if isinstance(values, dict):
                new_offsets = list(set(values.keys()) - set(self.values.keys()))
                if new_offsets and not self.mutable:
                    raise ParameterException(f"Offsets {new_offsets} not in range")
                self._process_values(values)
            else:
                if not isinstance(values, list):
                    values = [values]
                for idx, val in enumerate(values):
                    if address + idx not in self.values and not self.mutable:
                        raise ParameterException("Offset {address+idx} not in range")
                    self.values[address + idx] = val
            if use_as_default:
                for idx, val in iter(self.values.items()):
                    self.default_value[idx] = val
        except KeyError:
            return ExcCodes.ILLEGAL_ADDRESS
        return None

