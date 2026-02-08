"""Simulator data model implementation.

**REMARK** This class is internal to the server/simulator,.
"""
from __future__ import annotations

from ..constants import ExcCodes
from .simdevice import SimDevice, SimRegs


class SimCore:
    """Handler for the simulator/server."""

    class Runtime:
        """Memory setup for device."""

        _fx_mapper = {2: "d",  # Direct input
                    4: "i"}  # Input registers
        _fx_mapper.update([(i, "h")
                        for i in (3, 6, 16, 22, 23)])
        _fx_mapper.update([(i, "c")
                        for i in (1, 5, 15)])


        def __convert_to_bit(self, block: SimRegs):
            """Convert registers to bits."""
            new_flags = block[1]
            new_registers = block[2]
            return (block[0], new_flags, new_registers)

        def __init__(self, device: SimDevice):
            """Build device memory."""
            build = device.build_device()
            if not isinstance(build, dict):
                self.shared = True
                self.start_address = build[0]
                self.flags = build[1]
                self.registers = build[2]
                return
            self.shared = False
            self.block: dict[str, SimRegs] = {
                "c": self.__convert_to_bit(build["c"]),
                "d":  self.__convert_to_bit(build["d"]),
                "h": build["h"],
                "i": build["i"],
            }

        async def async_getValues(self, func_code: int, address: int, count: int = 1) -> list[int] | list[bool] | ExcCodes:
            """Get `count` values from datastore."""
            _ = func_code, address, count
            return [1]

        async def async_setValues(self, func_code: int, address: int, values: list[int] | list[bool] ) -> None | ExcCodes:
            """Set the datastore with the supplied values."""
            _ = func_code, address, values
            return None


    def __init__(self, devices: SimDevice | list[SimDevice]) -> None:
        """Build datastore."""
        if not isinstance(devices, list):
            if not isinstance(devices, SimDevice):
                raise TypeError("devices= is not a SimDevice or list of SimDevice entry")
            devices = [devices]
        self.devices: dict[int, SimCore.Runtime] = {}
        for inx, device in enumerate(devices):
            if not isinstance(device, SimDevice):
                raise TypeError(f"devices=list[{inx}] is not a SimDevice entry")
            if device.id in self.devices:
                raise TypeError(f"devices= device_id: {device.id} in multiple SimDevice entries")
            self.devices[device.id] = SimCore.Runtime(device)

    def __get_device(self, device_id: int) -> Runtime:
        """Return device object."""
        return self.devices[device_id] if device_id in self.devices else self.devices[0]

    async def async_getValues(self,device_id: int, func_code: int, address: int, count: int = 1) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore."""
        return await self.__get_device(device_id).async_getValues(func_code, address, count)

    async def async_setValues(self, device_id: int, func_code: int, address: int, values: list[int] | list[bool] ) -> None | ExcCodes:
        """Set the datastore with the supplied values."""
        return await self.__get_device(device_id).async_setValues(func_code, address, values)
