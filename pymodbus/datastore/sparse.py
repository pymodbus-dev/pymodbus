"""Modbus Sparse Datastore."""
# pylint: disable=missing-type-doc
from __future__ import annotations

from typing import Any

from ..constants import ExcCodes
from ..exceptions import ParameterException
from .store import BaseModbusDataBlock


class ModbusSparseDataBlock(BaseModbusDataBlock[dict[int, Any]]):
    """A sparse modbus datastore, silently redirected to ModbusSequentialBlock."""

    def __init__(self, values=None, mutable=True):
        """Initialize a sparse datastore."""
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

    async def async_getValues(self, address, count=1) -> list[int] | list[bool] | ExcCodes:
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

    async def async_setValues(self, address, values, use_as_default=False) -> None | ExcCodes:
        """Set the requested values of the datastore.

        :param address: The register starting address
        :param values: The new values to be set.
        :param use_as_default: Use the values as default

        Values can be given in different formats:
            - a single register value or
            - a list or tuple of contiguous register values, starting at
                given starting register address or
            - a dictionary of address:value(s) pairs, where value can be a
                single register or a list or tuple of contiguous registers.
        """
        try:
            if isinstance(values, dict):
                new_offsets = list(set(values.keys()) - set(self.values.keys()))
                if new_offsets and not self.mutable:
                    raise ParameterException(f"Offsets {new_offsets} not in range")
                self._process_values(values)
            else:
                if not isinstance(values, (list, tuple)):
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

