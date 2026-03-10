"""Modbus Sequential Datastore."""
from __future__ import annotations

from ..logging import Log
from ..simulator.simdata import DataType, SimData


class ModbusSequentialDataBlock:  # pylint: disable=too-few-public-methods
    """Creates a sequential modbus datastore."""

    def __init__(self, address, values):
        """Initialize the datastore.

        :param address: The starting address of the datastore
        :param values: Either a list or a dictionary of values
        """
        Log.warning("ModbusSequentialDataBlock is deprecated "
                    "and will be removed in v4.\n"
                    "Please convert to SimData/SimDevice.\n"
                    "Please read https://pymodbus.readthedocs.io/en/dev/source/upgrade_40.html#convert-to-simdata-simdevice")
        self.simdata = [SimData(address, values=values, datatype=DataType.REGISTERS)]
