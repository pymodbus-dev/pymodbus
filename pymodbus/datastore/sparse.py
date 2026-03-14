"""Modbus Sparse Datastore."""
from __future__ import annotations

from ..exceptions import ParameterException
from ..simulator.simdata import DataType, SimData


class ModbusSparseDataBlock:  # pylint: disable=too-few-public-methods
    """A sparse modbus datastore, silently redirected to ModbusSequentialBlock."""

    def __init__(self, values=None, mutable=True):
        """Initialize a sparse datastore."""
        _ = mutable
        self.simdata: list[SimData] = []
        self._process_values(values)

    def _process_values(self, values):
        """Process values."""

        def _process_as_dict(values):
            for idx, val in iter(values.items()):
                self.simdata.append(SimData(idx, values=val, datatype=DataType.REGISTERS))

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

