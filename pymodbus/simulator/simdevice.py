"""Simulator device model classes."""
from __future__ import annotations

from dataclasses import dataclass

from .simdata import SimData


@dataclass(order=True, frozen=True)
class SimDevice:
    """Configure a device with parameters and registers.

    Registers can be defined as shared or as 4 separate blocks.

    shared_block means all requests access the same registers,
    e.g. read_input_register and read_holding_register
    give the same result.

    .. warning:: Shared block cannot be mixed with non-shared blocks !

    In shared mode, individual coils/direct input are not addressed directly !
    Instead the register address is used with count and each register contains 16 bit.
    In non-shared mode coils/direct input can be addressed directly individually and
    each register contain 1 bit.

    **Device with shared registers**::

        SimDevice(
            id=1,
            block_shared=[SimData(...)]
        )

    **Device with non-shared registers**::

        SimDevice(
            id=1,
            block_coil=[SimData(...)],
            block_direct=[SimData(...)],
            block_holding=[SimData(...)],
            block_input=[SimData(...)],
        )

    A server can contain either a single :class:`SimDevice` or list of :class:`SimDevice`
    to simulate a multipoint line.

    .. warning:: each block is sorted by address !!
    """

    #: Address of device
    #:
    #: Default 0 means accept all devices, except those specifically defined.
    id: int = -1

    #: Enforce type checking, if True access are controlled to be conform with datatypes.
    #:
    #: Type violations like e.g. reading INT32 as INT16 are returned as ExceptionResponses,
    #: as well as being logged.
    type_check: bool = False

    #: Use this block for shared registers (Modern devices).
    #:
    #: Requests accesses all registers in this block.
    #:
    #: .. warning:: cannot be used together with other block_* parameters!
    block_shared: list[SimData] | None = None

    #: Use these blocks for devices which are divided in 4 blocks.
    #:
    #: block_coil and block_direct consist of coils/relays which each
    #: can be addressed.
    #:
    #: block_holding and block_input consist of registers.
    #:
    #: read/write_coil requests uses block_coil
    #: read/write_direct_input requests uses block_direct
    #: read/write_holding requests uses block_holding
    #: read/write_input requests uses block_input
    #:
    #: .. tip:: block_coil/direct/holding/input must all be defined
    block_coil: list[SimData] | None = None
    block_direct: list[SimData] | None = None
    block_holding: list[SimData] | None = None
    block_input: list[SimData] | None = None

    def __check_block(self, block: list[SimData] | None, name: str) -> list[SimData] | None:
        """Check block content."""
        if not block:
            return None
        if not isinstance(block, list):
            raise TypeError(f"{name} not a list")
        for entry in block:
            if not isinstance(entry, SimData):
                raise TypeError(f"{name} contains non SimData entries")
        block.sort(key=lambda x: x.address)
        return self.__check_block_entries(block, name)

    def __check_block_entries(self, block: list[SimData], name: str) -> list[SimData] | None:
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
                    continue
                raise TypeError(f"{name} contains multiple default SimData, not allowed")
            first = False
            if entry.address <= last_address:
                raise TypeError(f"{name} address {entry.address} is overlapping!")
            last_address = entry.address + entry.register_count -1
        if not block[0].default:
            default = SimData(address=block[0].address, count=last_address - block[0].address +1, default=True)
            block.insert(0, default)
        max_address = block[0].address + block[0].register_count -1
        if last_address > max_address:
            raise TypeError(f"{name} default set max address {max_address} but {last_address} is defined?")
        if len(block) > 1 and block[0].address > block[1].address:
            raise TypeError(f"{name} default set lowest address to {block[0].address} but {block[1].address} is defined?")
        return block

    def __post_init__(self):
        """Define a device."""
        if not isinstance(self.id, int) or not 0 <= self.id <= 255:
            raise TypeError("0 <= id < 255")
        non_shared = bool(self.block_coil) + bool(self.block_direct) + bool(self.block_holding) + bool(self.block_input)
        if self.block_shared and non_shared:
            raise TypeError("block_shared and non-shared blocks cannot be mixed")
        if 0 != non_shared != 4:
            raise TypeError("all 4 non-shared blocks must be defined")
        if not self.block_shared and not non_shared:
            raise TypeError("Either block_shared= or 4 non-shared blocks must be defined")

        super().__setattr__("block_shared", self.__check_block(self.block_shared, "block_shared"))
        super().__setattr__("block_coil", self.__check_block(self.block_coil, "block_coil"))
        super().__setattr__("block_direct", self.__check_block(self.block_direct, "block_direct"))
        super().__setattr__("block_holding", self.__check_block(self.block_holding, "block_holding"))
        super().__setattr__("block_input", self.__check_block(self.block_input, "block_input"))
