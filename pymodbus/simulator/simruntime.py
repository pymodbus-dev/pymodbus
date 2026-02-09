"""Simulator runtime implementation.

**REMARK** This class is internal to the server/simulator,.
"""
from __future__ import annotations

from ..constants import ExcCodes
from ..pdu import ExceptionResponse
from ..pdu.pdu import unpack_bitstring
from .simdevice import SimDevice, SimRegs
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
        b_h = build["h"]
        b_i = build["i"]
        self.block = {
            "c": self.convert_to_bit(build["c"]),
            "d":  self.convert_to_bit(build["d"]),
            "h": (b_h[0], len(b_h[1]), b_h[1],  b_h[2]),
            "i": (b_i[0], len(b_i[1]), b_i[1],  b_i[2]),
        }

    @classmethod
    def convert_to_bit(cls, block: SimRegs) -> tuple[int, int, list[int], list[int]]:
        """Convert registers to bits."""
        new_registers: list[int] = []
        for entry in block[2]:
            bool_list = unpack_bitstring(entry.to_bytes(2, byteorder="big"))
            for x in bool_list:
                new_registers.append(1 if x else 0)
        new_flags: list[int] = [block[1][0]]*len(new_registers)
        return (block[0], len(new_flags), new_flags, new_registers)


    async def get_block(self, func_code: int, address: int, count: int, values: list[int] | None) -> list[int] | ExceptionResponse:
        """Calculate offset."""
        block_id = "x" if self.shared else self._fx_mapper[func_code]
        start_address, register_count, registers, flags = self.block[block_id]
        offset = address - start_address
        if values:
            count = len(values)
        if address > start_address + register_count or address < start_address or offset + count > register_count:
            return ExceptionResponse(func_code, ExcCodes.ILLEGAL_ADDRESS)
        if self.action:
            result = await self.action(func_code, address, registers, None)
            if isinstance(result, ExceptionResponse):
                return result
            if result:
                values = result
        for i in range(count):
            addr = offset + i
            if flags[addr] & SimUtils.RunTimeFlag_TYPE == DataType.INVALID:
                return ExceptionResponse(func_code, ExcCodes.ILLEGAL_ADDRESS)
            if values:
                if flags[addr] & SimUtils.RunTimeFlag_READONLY:
                    return ExceptionResponse(func_code, ExcCodes.ILLEGAL_ADDRESS)
                registers[addr] = values[i]
        return registers[offset:offset+count]

    async def async_getValues(self, func_code: int, address: int, count: int) -> list[int] | ExceptionResponse:
        """Get `count` values from datastore."""
        return await self.get_block(func_code, address, count, None)

    async def async_setValues(self, func_code: int, address: int, values: list[int] ) -> None | ExceptionResponse:
        """Set the datastore with the supplied values."""
        count = len(values)
        block = await self.get_block(func_code, address, count, values)
        return block if isinstance(block, ExceptionResponse) else None

