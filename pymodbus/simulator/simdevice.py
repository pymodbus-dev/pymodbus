"""Simulator device model classes."""
from __future__ import annotations

from dataclasses import dataclass

from .simdata import SimData


OFFSET_NONE = (-1, -1, -1, -1)

@dataclass(order=True, frozen=True)
class SimDevice:
    """Configure a device with parameters and registers.

    Registers are always defined as one block.

    Some old devices uses 4 distinct blocks instead of 1 block, to
    support these devices, define 1 large block consisting of the
    4 blocks and use the offset_*= parameters.

    When using distinct blocks, coils and direct inputs are addressed differently,
    each register represent 1 coil/relay.

    **Device with shared registers**::

        SimDevice(
            id=1,
            registers=[SimData(...)]
        )

    **Device with non-shared registers**::

        SimDevice(
            id=1,
            registers=[SimData(...)],
            non_shared_mode=True,
            offset_coil=0,
            offset_direct=10,
            offset_holding=20,
            offset_input=30,
        )

    Meaning registers:

        - 0-9 are coils
        - 10-19 are relays
        - 20-29 are holding registers
        - 30-.. are input registers

    A server can contain either a single :class:`SimDevice` or list of :class:`SimDevice`
    to simulate a multipoint line.

    .. warning:: each block is sorted by address !!
    """

    #: Address/id of device
    #:
    #: Default 0 means accept all devices, except those specifically defined.
    id: int

    #: List of registers.
    #:
    registers: list[SimData]

    #: Use this for old devices with 4 blocks.
    #:
    #: .. tip:: content is (coil, direct, holding, input)
    offset_address: tuple[int, int, int, int] = OFFSET_NONE

    #: Enforce type checking, if True access are controlled to be conform with datatypes.
    #:
    #: Type violations like e.g. reading INT32 as INT16 are returned as ExceptionResponses,
    #: as well as being logged.
    type_check: bool = False


    def __check_block(self, block: list[SimData]) -> list[SimData]:
        """Check block content."""
        for inx, entry in enumerate(block):
            if not isinstance(entry, SimData):
                raise TypeError(f"registers[{inx}]= is a SimData entry")
        block.sort(key=lambda x: x.address)
        return self.__check_block_entries(block)

    def __check_block_entries(self, block: list[SimData]) -> list[SimData]:
        """Check block entries."""
        last_address = -1
        if len(block) > 1 and block[1].default:
            temp = block[0]
            block[0] = block[1]
            block[1] = temp
        first = True
        for entry in block:
            if entry.default:
                if first:
                    first = False
                    continue
                raise TypeError("Multiple default SimData, not allowed")
            first = False
            if entry.address <= last_address:
                raise TypeError("SimData address {entry.address} is overlapping!")
            last_address = entry.address + entry.register_count -1
        if not block[0].default:
            default = SimData(address=block[0].address, count=last_address - block[0].address +1, default=True)
            block.insert(0, default)
        max_address = block[0].address + block[0].register_count -1
        if last_address > max_address:
            raise TypeError("Default set max address {max_address} but {last_address} is defined?")
        if len(block) > 1 and block[0].address > block[1].address:
            raise TypeError("Default set lowest address to {block[0].address} but {block[1].address} is defined?")
        return block

    def __post_init__(self):
        """Define a device."""
        if not isinstance(self.id, int) or not 0 <= self.id <= 255:
            raise TypeError("0 <= id < 255")
        if not isinstance(self.registers, list) or not self.registers:
            raise TypeError("registers= not a list")
        if not isinstance(self.type_check, bool):
            raise TypeError("type_check= not a bool")
        super().__setattr__("registers", self.__check_block(self.registers))
        if self.offset_address != OFFSET_NONE:
            if len(self.offset_address) != 4:
                raise TypeError("offset_address= must have 4 addresses")
            reg_start = self.registers[0].address
            reg_end = self.registers[0].address + self.registers[0].register_count
            for i in range(4):
                if not (reg_start < self.offset_address[i] < reg_end):
                    raise TypeError(f"offset_address[{i}] outside defined range")
                if i and self.offset_address[i-1] >= self.offset_address[i]:
                    raise TypeError("offset_address= must be ascending addresses")
