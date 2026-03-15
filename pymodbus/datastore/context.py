"""Context for datastore."""

from __future__ import annotations

from copy import deepcopy

from ..constants import ExcCodes
from ..exceptions import NoSuchIdException
from ..logging import Log
from ..simulator.simdata import DataType
from ..simulator.simdevice import SimDevice
from .sequential import ModbusSequentialDataBlock
from .simulator import ModbusSimulatorContext
from .sparse import ModbusSparseDataBlock


class ModbusDeviceContext:   # pylint: disable=too-few-public-methods
    """Create a modbus data model with data stored in a block.

    :param di: discrete inputs initializer ModbusDataBlock
    :param co: coils initializer ModbusDataBlock
    :param hr: holding register initializer ModbusDataBlock
    :param ir: input registers initializer ModbusDataBlock
    """

    _fx_mapper = {2: "d", 4: "i"}
    _fx_mapper.update([(i, "h") for i in (3, 6, 16, 22, 23)])
    _fx_mapper.update([(i, "c") for i in (1, 5, 15)])

    def __build_data(self, simdata):
        """Build and/or correct values."""
        for entry in simdata:
            entry.datatype = DataType.BITS
            if not isinstance(entry.values, list):
                entry.values = [entry.values]
            for i, _value in enumerate(entry.values):
                entry.values[i] = bool(entry.values[i])

    def __init__(self, *_args,
                    di: ModbusSequentialDataBlock | ModbusSparseDataBlock | None = None,
                    co: ModbusSequentialDataBlock | ModbusSparseDataBlock | None = None,
                    ir: ModbusSequentialDataBlock | ModbusSparseDataBlock | None = None,
                    hr: ModbusSequentialDataBlock | ModbusSparseDataBlock | None = None,
                ):
        """Define device."""
        if not di:
            di = ModbusSequentialDataBlock(1, values=False)
        if not co:
            co = ModbusSequentialDataBlock(1, values=False)
        if not ir:
            ir = ModbusSequentialDataBlock(1, values=0)
        if not hr:
            hr = ModbusSequentialDataBlock(1, values=0)
        co_simdata = deepcopy(co.simdata)
        di_simdata = deepcopy(di.simdata)
        ir_simdata = deepcopy(ir.simdata)
        hr_simdata = deepcopy(hr.simdata)
        self.__build_data(co_simdata)
        self.__build_data(di_simdata)
        self.simdevice = SimDevice(0, simdata=(
            co_simdata,
            di_simdata,
            ir_simdata,
            hr_simdata))
        Log.warning("ModbusDeviceContext, ModbusSequentialDataBlock, "
                    "ModbusSparseDataBlock are deprecated "
                    "and will be removed in v4.\n"
                    "Please convert to SimData/SimDevice.\n"
                    "Please read https://pymodbus.readthedocs.io/en/dev/source/upgrade_40.html#convert-to-simdata-simdevice")


class ModbusServerContext:
    """This represents a master collection of device contexts.

    If single is set to true, it will be treated as a single
    context so every device id returns the same context. If single
    is set to false, it will be interpreted as a collection of
    device contexts.
    """

    def __init__(self, devices=None, single=True):
        """Initialize a new instance of a modbus server context.

        :param devices: A dictionary of client contexts
        :param single: Deprecated

        dev_id=0 is automatically used when devices= is a ModbusDeviceContext
        and not a dict.
        """
        _ = single
        if not devices:
            raise TypeError("devices= cannot be None")
        self._devices: dict[int, ModbusDeviceContext]
        self.simdevices: list[SimDevice] = []
        if isinstance(devices, dict):
            self._devices = devices
            for dev_id, entry in devices.items():
                if not isinstance(entry, ModbusSimulatorContext):
                    entry.id = dev_id
                    self.simdevices.append(entry)
        else:
            self._devices = {0: devices}
            if not isinstance(devices, ModbusSimulatorContext):
                self.simdevices = [devices.simdevice]
        Log.warning("ModbusServerContext is deprecated "
                    "and will be removed in v4.\n"
                    "Please convert to SimData/SimDevice.\n"
                    "Please read https://pymodbus.readthedocs.io/en/dev/source/upgrade_40.html#convert-to-simdata-simdevice")

    def __get_device(self, device_id: int) -> ModbusDeviceContext:
        """Return device object."""
        if device_id in self._devices:
            return self._devices[device_id]
        if 0 in self._devices:
            return self._devices[0]
        raise NoSuchIdException(
            f"device_id - {device_id} does not exist, or is out of range"
        )

    async def async_getValues(self, device_id: int, func_code: int, address: int, count: int = 1) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore.

        :param device_id: the device being addressed
        :param func_code: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        dev = self.__get_device(device_id)
        if isinstance(dev, ModbusSimulatorContext):
            return await dev.async_OLD_getValues(func_code, address, count)
        return ExcCodes.DEVICE_BUSY

    async def async_setValues(self, device_id: int, func_code: int, address: int, values: list[int] | list[bool] ) -> None | ExcCodes:
        """Set the datastore with the supplied values.

        :param device_id: the device being addressed
        :param func_code: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        dev = self.__get_device(device_id)
        if isinstance(dev, ModbusSimulatorContext):  # pragma: no cover
            return await dev.async_OLD_setValues(func_code, address, values)
        return ExcCodes.DEVICE_BUSY

    def device_ids(self):
        """Get the configured device ids."""
        return list(self._devices.keys())
