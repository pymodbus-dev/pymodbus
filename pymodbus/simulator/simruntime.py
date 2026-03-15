"""Simulator runtime implementation.

**REMARK** This class is internal to the server/simulator,.
"""
from __future__ import annotations

from ..constants import ExcCodes
from .simdevice import SimDevice
from .simutils import DataType, SimUtils


class SimRuntime:
    """Memory setup for device."""

    _fx_mapper = {2: "d",  # Direct input
                4: "i"}  # Input registers
    _fx_mapper.update([(i, "h")
                    for i in (3, 6, 16, 22, 23)])
    _fx_mapper.update([(i, "c")
                    for i in (1, 5, 15)])


    def __init__(self, device: SimDevice):
        """Build device memory."""
        self.action = device.action
        build = device.build_device()
        self.block: dict[str, tuple[int, int, list[int], list[int]]] = {}
        if not isinstance(build, dict):
            self.shared = True
            self.block["x"] = (
                build[0],
                len(build[2]),
                build[1],
                build[2],
            )
            return
        self.shared = False
        self.block = {}
        for i in ("c", "d", "h", "i"):
            x = build[i]
            self.block[i] =  (x[0], len(x[1]), x[1],  x[2])

    async def get_block(self, func_code: int, address: int, count: int, values: list[int] | list[bool] | None) -> list[int] | list[bool] | ExcCodes:
        """Calculate offset."""
        block_id = "x" if self.shared else self._fx_mapper[func_code]
        start_address, register_count, registers, flags = self.block[block_id]
        offset = address - start_address
        if values:
            count = len(values)
        if address > start_address + register_count or address < start_address or offset + count > register_count:
            return ExcCodes.ILLEGAL_ADDRESS
        if self.action:
            result = await self.action(func_code, address, registers, None)
            if isinstance(result, ExcCodes):
                return result
            if result:
                values = result
        for i in range(count):
            addr = offset + i
            if flags[addr] & SimUtils.RunTimeFlag_TYPE == DataType.INVALID:
                return ExcCodes.ILLEGAL_ADDRESS
            if values:
                if flags[addr] & SimUtils.RunTimeFlag_READONLY:
                    return ExcCodes.ILLEGAL_ADDRESS
                registers[addr] = values[i]
        return registers[offset:offset+count]

    async def async_getValues(self, func_code: int, address: int, count: int) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore."""
        return await self.get_block(func_code, address, count, None)

    async def async_setValues(self, func_code: int, address: int, values: list[int] | list[bool] ) -> None | ExcCodes:
        """Set the datastore with the supplied values."""
        count = len(values)
        block = await self.get_block(func_code, address, count, values)
        return block if isinstance(block, ExcCodes) else None

