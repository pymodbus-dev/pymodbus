"""Context for datastore."""

from __future__ import annotations

from ..constants import ExcCodes
from ..exceptions import NoSuchIdException
from ..logging import Log
from .sequential import ModbusSequentialDataBlock
from .sparse import ModbusSparseDataBlock


# pylint: disable=missing-type-doc

class ModbusDeviceContext:
    """Create a modbus data model with data stored in a block.

    :param di: discrete inputs initializer ModbusDataBlock
    :param co: coils initializer ModbusDataBlock
    :param hr: holding register initializer ModbusDataBlock
    :param ir: input registers initializer ModbusDataBlock
    """

    _fx_mapper = {2: "d", 4: "i"}
    _fx_mapper.update([(i, "h") for i in (3, 6, 16, 22, 23)])
    _fx_mapper.update([(i, "c") for i in (1, 5, 15)])

    def __init__(self, *_args,
                    di: ModbusSequentialDataBlock | ModbusSparseDataBlock | None = None,
                    co: ModbusSequentialDataBlock | ModbusSparseDataBlock | None = None,
                    ir: ModbusSequentialDataBlock | ModbusSparseDataBlock | None = None,
                    hr: ModbusSequentialDataBlock | ModbusSparseDataBlock | None = None,
                ):
        """Initialize the datastores."""
        self.store = {
            "d": di,
            "c": co,
            "i": ir,
            "h": hr,
        }

    async def async_OLD_getValues(self, func_code, address, count=1) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore.

        :param func_code: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        address += 1
        Log.debug("getValues: fc-[{}] address-{}: count-{}", func_code, address, count)
        if dt := self.store[self._fx_mapper.get(func_code, "x")]:
            return await dt.async_OLD_getValues(address, count)
        return ExcCodes.ILLEGAL_ADDRESS

    async def async_OLD_setValues(self, func_code, address, values) -> None | ExcCodes:
        """Set the datastore with the supplied values.

        :param func_code: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        address += 1
        Log.debug("setValues[{}] address-{}: count-{}", func_code, address, len(values))
        if dt := self.store[self._fx_mapper.get(func_code, "x")]:
            return await dt.async_OLD_setValues(address, values)
        return ExcCodes.ILLEGAL_ADDRESS


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
        :param single: Set to true to treat this as a single context
        """
        self.single = single
        self._devices: dict = devices or {}
        if self.single:
            self._devices = {0: self._devices}

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
        return await dev.async_OLD_getValues(func_code, address, count)

    async def async_setValues(self, device_id: int, func_code: int, address: int, values: list[int] | list[bool] ) -> None | ExcCodes:
        """Set the datastore with the supplied values.

        :param device_id: the device being addressed
        :param func_code: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        dev = self.__get_device(device_id)
        return await dev.async_OLD_setValues(func_code, address, values)

    def device_ids(self):
        """Get the configured device ids."""
        return list(self._devices.keys())
