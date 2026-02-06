"""Simulator data model implementation.

**REMARK** This class is internal to the server/simulator,.
"""
from __future__ import annotations

from ..constants import ExcCodes
from .simdevice import SimDevice


class SimCore:
    """Handler for the simulator/server."""

    _fx_mapper = {2: "d", 4: "i"}
    _fx_mapper.update([(i, "h") for i in (3, 6, 16, 22, 23)])
    _fx_mapper.update([(i, "c") for i in (1, 5, 15)])

    class Runtime:  # pylint: disable=too-few-public-methods
        """Memory setup for device."""

        def __init__(self):
            """Build device memory."""


    def __init__(self, devices: SimDevice | list[SimDevice]) -> None:
        """Build datastore."""
        if not isinstance(devices, list):
            if not isinstance(devices, SimDevice):
                raise TypeError("devices= is not a SimDevice or list of SimDevice entry")
            devices = [devices]
        device_ids: list[int] = []
        for inx, device in enumerate(devices):
            if not isinstance(device, SimDevice):
                raise TypeError(f"devices=list[{inx}] is not a SimDevice entry")
            if device.id in device_ids:
                raise TypeError(f"devices= device_id: {device.id} repeated in multiple SimDevice entries")

    def __decode(self, fx: int) -> str:
        """Convert the function code to the datastore to.

        :param fx: The function we are working with
        :returns: one of [d(iscretes),i(nputs),h(olding),c(oils)
        """
        return self._fx_mapper.get(fx, "x")

    async def async_getValues(self, device_id: int, func_code: int, address: int, count: int = 1) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore.

        :param device_id: the device being addressed
        :param func_code: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        _ = device_id, func_code, address, count
        self.__decode(0)
        return [1]

    async def async_setValues(self, device_id: int, func_code: int, address: int, values: list[int] | list[bool] ) -> None | ExcCodes:
        """Set the datastore with the supplied values.

        :param device_id: the device being addressed
        :param func_code: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        _ = device_id, func_code, address, values
        return None
