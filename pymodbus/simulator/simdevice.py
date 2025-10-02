"""Simulator device model classes."""
from __future__ import annotations

from dataclasses import dataclass

from .simdata import SimData


@dataclass(frozen=True)
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
    """

    #: Address of device
    #:
    #: Default 0 means accept all devices, except those specifically defined.
    id: int = 0

    #: Enforce type checking, if True access are controlled to be conform with datatypes.
    #:
    #: Used to control that e.g. INT32 are not read as INT16.
    type_check: bool = False

    #: Use this block for shared registers (Modern devices).
    #:
    #: Requests accesses all registers in this block.
    #:
    #: .. warning:: cannot be used together with other block_* parameters!
    block_shared: list[SimData] | None = None

    #: Use this block for devices which are divided in 4 blocks.
    #:
    #: In this block an address is a single coil, there are no registers.
    #:
    #: Request of type read/write_coil accesses this block.
    #:
    #: .. tip:: block_coil/direct/holding/input must all be defined
    block_coil: list[SimData] | None = None

    #: Use this block for devices which are divided in 4 blocks.
    #:
    #: In this block an address is a single relay, there are no registers.
    #:
    #: Request of type read/write_direct_input accesses this block.
    #:
    #: .. tip:: block_coil/direct/holding/input must all be defined
    block_direct: list[SimData] | None = None

    #: Use this block for devices which are divided in 4 blocks.
    #:
    #: In this block an address is a register.
    #:
    #: Request of type read/write_holding accesses this block.
    #:
    #: .. tip:: block_coil/direct/holding/input must all be defined
    block_holding: list[SimData] | None = None

    #: Use this block for non-shared registers (very old devices).
    #:
    #: In this block an address is a register.
    #:
    #: Request of type read/write_input accesses this block.
    #:
    #: .. tip:: block_coil/direct/holding/input must all be defined
    block_input: list[SimData] | None = None

    def __post_init__(self):
        """Define a device."""
        if not isinstance(self.id, int) or 255 < self.id < 0:
            raise TypeError("0 <= id < 255")
        blocks = (self.block_coil, self.block_direct, self.block_holding, self.block_input)
        if self.block_shared:
            if not isinstance(self.block_shared, list):
                raise TypeError("block_shared must be a list")
            for entry in blocks:
                if entry:
                    raise TypeError(f"{entry} cannot be combined with block_shared")
            return
        for entry in blocks:
            if not entry or not isinstance(entry, list):
                raise TypeError(f"{entry} not defined or not a list")
