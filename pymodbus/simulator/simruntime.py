"""Simulator runtime implementation.

**REMARK** This class is internal to the server/simulator,.
"""
from __future__ import annotations

from ..constants import ExcCodes
from .simdevice import SimDevice
from .simutils import DataType, SimUtils


class SimRuntime:
    """Memory setup for device."""

    _fx_mapper = {2: "d", 4: "i"} # Direct input and Input registers
    _fx_mapper.update([(i, "h") # Holding registers
                    for i in (3, 6, 16, 22, 23)])
    _fx_mapper.update([(i, "c") # Coils
                    for i in (1, 5, 15)])


    def __init__(self, device: SimDevice):
        """Build device memory."""
        self.action = device.action
        self.use_bit_addressing = device.use_bit_addressing
        build = device.build_device()
        self.block: dict[str, tuple[int, int, list[int], list[int]]] = {}
        if not isinstance(build, dict):
            self.block["x"] = (
                build[0],
                len(build[2]),
                build[1],
                build[2],
            )
            return
        for i in ("c", "d", "h", "i"):
            self.block[i] = (build[i][0], len(build[i][1]), build[i][1],  build[i][2])

    async def __check_block(self, func_code: int, block_id: str, address: int, count: int,  offset: int, values: list[int] | list[bool] | None) -> ExcCodes | None:
        """Check block request."""
        start_address, _, registers, flags = self.block[block_id]
        if self.action and (result := await self.action(func_code, start_address, address, count, registers, values)):
            return result
        for i in range(count):
            addr = offset + i
            if flags[addr] & SimUtils.RunTimeFlag_TYPE == DataType.INVALID:
                return ExcCodes.ILLEGAL_ADDRESS
            if values:
                if flags[addr] & SimUtils.RunTimeFlag_READONLY:
                    return ExcCodes.ILLEGAL_ADDRESS
                registers[addr] = values[i]
        return None

    async def get_block(self, func_code: int, address: int, count: int, values: list[int] | list[bool] | None) -> list[int] | list[bool] | ExcCodes:
        """Calculate offset."""
        fc_block = self._fx_mapper.get(func_code, "x")
        block_id = "x" if "x" in self.block else fc_block
        use_bits =  fc_block in {"c", "d"} and self.use_bit_addressing
        start_address, register_count, registers, _ = self.block[block_id]
        if use_bits:
            offset = int(address / 16) - start_address
            effective_count = int(count / 16) + 1
        else:
            offset = address - start_address
            effective_count = count
        if register_count <= offset < 0 or offset + effective_count > register_count:
            return ExcCodes.ILLEGAL_ADDRESS
        if (result := await self.__check_block(func_code, block_id, address, count, offset, values)):
            return result
        if fc_block in {"c", "d"}:
            list_bools = SimUtils.registersToBits(registers[offset:offset+count])
            if not use_bits:
                return list_bools
            bit_offset = address % 16
            return list_bools[bit_offset:bit_offset+count]
        return registers[offset:offset+count]

    async def async_getValues(self, func_code: int, address: int, count: int) -> list[int] | list[bool] | ExcCodes:
        """Get `count` values from datastore."""
        return await self.get_block(func_code, address, count, None)

    async def async_setValues(self, func_code: int, address: int, values: list[int] | list[bool] ) -> None | ExcCodes:
        """Set the datastore with the supplied values."""
        block = await self.get_block(func_code, address, len(values), values)
        return block if isinstance(block, ExcCodes) else None

