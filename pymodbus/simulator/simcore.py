"""Simulator data model implementation.

**REMARK** This class is internal to the server/simulator,.
"""
from __future__ import annotations

from ..pdu import ExceptionResponse
from .simdevice import SimDevice
from .simruntime import SimRuntime


class SimCore:
    """Handler for the simulator/server."""

    def __init__(self, devices: SimDevice | list[SimDevice]) -> None:
        """Build datastore."""
        if not isinstance(devices, list):
            if not isinstance(devices, SimDevice):
                raise TypeError("devices= is not a SimDevice or list of SimDevice entry")
            devices = [devices]
        self.devices: dict[int, SimRuntime] = {}
        for inx, device in enumerate(devices):
            if not isinstance(device, SimDevice):
                raise TypeError(f"devices=list[{inx}] is not a SimDevice entry")
            if device.id in self.devices:
                raise TypeError(f"devices= device_id: {device.id} in multiple SimDevice entries")
            self.devices[device.id] = SimRuntime(device)

    def __get_device(self, device_id: int) -> SimRuntime:
        """Return device object."""
        return self.devices[device_id] if device_id in self.devices else self.devices[0]

    async def async_getValues(self,device_id: int, func_code: int, address: int, count: int = 1) -> list[int] | ExceptionResponse:
        """Get `count` values from datastore."""
        return await self.__get_device(device_id).async_getValues(func_code, address, count)

    async def async_setValues(self, device_id: int, func_code: int, address: int, values: list[int] ) -> None | ExceptionResponse:
        """Set the datastore with the supplied values."""
        return await self.__get_device(device_id).async_setValues(func_code, address, values)
