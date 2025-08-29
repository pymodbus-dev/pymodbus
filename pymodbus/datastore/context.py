"""Context for datastore."""

from __future__ import annotations

from pymodbus.constants import ExcCodes
from pymodbus.exceptions import NoSuchIdException
from pymodbus.logging import Log

from .sequential import ModbusSequentialDataBlock
from .store import BaseModbusDataBlock


# pylint: disable=missing-type-doc

class ModbusBaseDeviceContext:
    """Interface for a modbus device data context.

    Derived classes must implemented the following methods:
            reset(self)
            getValues/async_getValues(self, func_code, address, count=1)
            setValues/async_setValues(self, func_code, address, values)
    """

    _fx_mapper = {2: "d", 4: "i"}
    _fx_mapper.update([(i, "h") for i in (3, 6, 16, 22, 23)])
    _fx_mapper.update([(i, "c") for i in (1, 5, 15)])

    def decode(self, fx):
        """Convert the function code to the datastore to.

        :param fx: The function we are working with
        :returns: one of [d(iscretes),i(nputs),h(olding),c(oils)
        """
        return self._fx_mapper.get(fx, "x")

    async def async_getValues(self, func_code: int, address: int, count: int = 1) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore.

        :param func_code: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        return self.getValues(func_code, address, count)

    async def async_setValues(self, func_code: int, address: int, values: list[int] | list[bool] ) -> None | ExcCodes:
        """Set the datastore with the supplied values.

        :param func_code: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        return self.setValues(func_code, address, values)

    def getValues(self, func_code: int, address: int, count: int = 1) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore.

        :param func_code: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        Log.error("getValues({},{},{}) not implemented!", func_code, address, count)
        return ExcCodes.ILLEGAL_FUNCTION

    def setValues(self, func_code: int, address: int, values: list[int] | list[bool]) -> None | ExcCodes:
        """Set the datastore with the supplied values.

        :param func_code: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        Log.error("setValues({},{},{}) not implemented!", func_code, address, values)
        return ExcCodes.ILLEGAL_FUNCTION


# ---------------------------------------------------------------------------#
#  Device Contexts
# ---------------------------------------------------------------------------#
class ModbusDeviceContext(ModbusBaseDeviceContext):
    """Create a modbus data model with data stored in a block.

    :param di: discrete inputs initializer ModbusDataBlock
    :param co: coils initializer ModbusDataBlock
    :param hr: holding register initializer ModbusDataBlock
    :param ir: input registers initializer ModbusDataBlock
    """

    def __init__(self, *_args,
                    di: BaseModbusDataBlock | None = None,
                    co: BaseModbusDataBlock | None = None,
                    ir: BaseModbusDataBlock | None = None,
                    hr: BaseModbusDataBlock | None = None,
                ):
        """Initialize the datastores."""
        self.store = {}
        self.store["d"] = di if di is not None else ModbusSequentialDataBlock.create()
        self.store["c"] = co if co is not None else ModbusSequentialDataBlock.create()
        self.store["i"] = ir if ir is not None else ModbusSequentialDataBlock.create()
        self.store["h"] = hr if hr is not None else ModbusSequentialDataBlock.create()

    def __str__(self):
        """Return a string representation of the context.

        :returns: A string representation of the context
        """
        return "Modbus device Context"

    def reset(self):
        """Reset all the datastores to their default values."""
        for datastore in iter(self.store.values()):
            datastore.reset()

    def getValues(self, func_code, address, count=1) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore.

        :param func_code: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        address += 1
        Log.debug("getValues: fc-[{}] address-{}: count-{}", func_code, address, count)
        return self.store[self.decode(func_code)].getValues(address, count)

    def setValues(self, func_code, address, values) -> None | ExcCodes:
        """Set the datastore with the supplied values.

        :param func_code: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        address += 1
        Log.debug("setValues[{}] address-{}: count-{}", func_code, address, len(values))
        return self.store[self.decode(func_code)].setValues(address, values)

    def register(self, function_code, func_code, datablock=None):
        """Register a datablock with the device context.

        :param function_code: function code (int)
        :param func_code: string representation of function code (e.g "cf" )
        :param datablock: datablock to associate with this function code
        """
        self.store[func_code] = datablock or ModbusSequentialDataBlock.create()
        self._fx_mapper[function_code] = func_code


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
        self._devices = devices or {}
        if self.single:
            self._devices = {0: self._devices}

    def __iter__(self):
        """Iterate over the current collection of device contexts.

        :returns: An iterator over the device contexts
        """
        return iter(self._devices.items())

    def __contains__(self, device_id):
        """Check if the given device_id is in this list.

        :param device_id: device_id The device_id to check for existence
        :returns: True if the device_id exists, False otherwise
        """
        if self.single and self._devices:
            return True
        return device_id in self._devices

    def __setitem__(self, device_id, context):
        """Use to set a new device_id context.

        :param device_id: The device_id context to set
        :param context: The new context to set for this device_id
        :raises NoSuchIdException:
        """
        if self.single:
            device_id = 0
        if 0xF7 >= device_id >= 0x00:
            self._devices[device_id] = context
        else:
            raise NoSuchIdException(f"device_id index :{device_id} out of range")

    def __delitem__(self, device_id):
        """Use to access the device_id context.

        :param device_id: The device context to remove
        :raises NoSuchIdException:
        """
        if not self.single and (0xF7 >= device_id >= 0x00):
            del self._devices[device_id]
        else:
            raise NoSuchIdException(f"device_id index: {device_id} out of range")

    def __getitem__(self, device_id):
        """Use to get access to a device_id context.

        :param device_id: The device context to get
        :returns: The requested device context
        :raises NoSuchIdException:
        """
        if self.single:
            device_id = 0
        if device_id in self._devices:
            return self._devices.get(device_id)
        raise NoSuchIdException(
            f"device_id - {device_id} does not exist, or is out of range"
        )

    def device_ids(self):
        """Define device_ids."""
        return list(self._devices.keys())
