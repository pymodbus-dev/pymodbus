"""Modbus Sequential Datastore."""
from __future__ import annotations

from ..simulator.simdata import DataType, SimData


class ModbusSequentialDataBlock:  # pylint: disable=too-few-public-methods
    """Creates a sequential modbus datastore."""

    def __init__(self, address, values):
        """Initialize the datastore.

        :param address: The starting address of the datastore
        :param values: Either a list or a dictionary of values
        """
        self.simdata = [SimData(address-1, values=values, datatype=DataType.REGISTERS)]
