"""Simulator data model classes."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class SimDataType(Enum):
    """Register types, used to define group of registers.

    This is the types pymodbus recognizes, actually the modbus standard do NOT define e.g. INT32,
    but since nearly every device have e.g. INT32 as part of its register map, it was decided to
    include it in pymodbus, with automatic conversions to/from registers.
    """

    #: 1 integer == 1 register
    INT16 = 1
    #: 1 positive integer == 1 register
    UINT16 = 2
    #: 1 integer == 2 registers
    INT32 = 3
    #: 1 positive integer == 2 register2
    UINT32 = 4
    #: 1 integer == 4 registers
    INT64 = 5
    #: 1 positive integer == 4 register
    UINT64 = 6
    #: 1 float == 2 registers
    FLOAT32 = 7
    #: 1 float == 4 registers
    FLOAT64 = 8
    #: 1 string == len(string) / 2 registers
    #:
    #: .. tip:: String length must be a multiple of 2 (corresponding to registers).
    STRING = 9
    #: Shared mode: 16 bits == 1 register else 1 bit == 1 "register" (address)
    BITS = 10
    #: Raw registers
    #:
    #: .. warning:: Do not use as default, since it fills the memory and block other registrations.
    REGISTERS = 11
    #: Raw registers, but also sets register address limits.
    #:
    #: .. tip:: It a single but special register, and therefore improves speed and memory usage compared to REGISTERS.
    DEFAULT = 12

@dataclass(frozen=True)
class SimData:
    """Configure a group of continuous identical registers.

    **Example**:

    .. code-block:: python

        SimData(
            start_register=100,
            count=5,
            value=-123456
            datatype=SimDataType.INT32
        )

    The above code defines 5 INT32, each with the value -123456, in total 20 registers.

    .. tip:: use SimDatatype.DEFAULT to define register limits:

    .. code-block:: python

        SimData(
            start_register=0, # First legal registers
            count=1000,       # last legal register is start_register+count-1
            value=0x1234      # Default register value
            datatype=SimDataType.DEFAULT
        )

    The above code sets the range of legal registers to 0..9999 all with the value 0x1234.
    Accessing non-defined registers will cause an exception response.

    .. attention:: Using SimDataType.DEFAULT is a LOT more efficient to define all registers, than \
    the other datatypes. This is because default registers are not created unless written to, whereas \
    the registers of other datatypes are each created as objects.
    """

    #: Address of first register, starting with 0.
    #:
    #: .. caution:: No default, must be defined.
    start_register: int

    #: Value of datatype, to initialize the registers (repeated with count, apart from string).
    #:
    #: Depending on in which block the object is used some value types are not legal e.g. float cannot
    #: be used to define coils.
    value: int | float | str | bool | bytes = 0

    #: Count of datatype e.g. count=3 datatype=SimdataType.INT32 is 6 registers.
    #:
    #: SimdataType.STR is special:
    #:
    #: - count=1, value="ABCD" is 2 registers
    #: - count=3, value="ABCD" is 6 registers, with "ABCD" repeated 3 times.
    count: int = 1

    #: Datatype, used to check access and calculate register count.
    #:
    #: .. note:: Default is SimDataType.REGISTERS
    datatype: SimDataType = SimDataType.REGISTERS

    #: Optional function to call when registers are being read/written.
    #:
    #: **Example function:**
    #:
    #: .. code-block:: python
    #:
    #:     def my_action(
    #:        addr: int,
    #:        value: int | float | str | bool | bytes
    #:    ) -> int | float | str | bool | bytes:
    #:         return value + 1
    #:
    #: .. tip:: use functools.partial to add extra parameters if needed.
    action: Callable[[int, int | float | str | bool | bytes], int | float | str | bool | bytes] | None = None

    def __post_init__(self):
        """Define a group of registers."""
        if not isinstance(self.start_register, int) or not 0 <= self.start_register < 65535:
            raise TypeError("0 <= start_register < 65535")
        if not isinstance(self.count, int) or not 0 < self.count <= 65535:
            raise TypeError("0 < count <= 65535")
        if not isinstance(self.datatype, SimDataType):
            raise TypeError("datatype not SimDataType")
        if self.action and not callable(self.action):
            raise TypeError("action not Callable")


@dataclass(frozen=True)
class SimDevice:
    """Configure a device with parameters and registers.

    Registers can be defined as shared or as 4 separate blocks.

    shared_block means all requests access the same registers,
    allowing e.g. coils to be read as a holding register (except if type_checking is True).

    .. warning:: Shared mode cannot be mixed with non-shared mode !

    In shared mode, individual coils/direct input cannot be addressed directly ! Instead
    the register address is used with count. In non-shared mode coils/direct input can be
    addressed directly.

    **Device with shared registers**::

        SimDevice(
            id=0,
            block_shared=[SimData(...)]
        )

    **Device with non-shared registers**::

        SimDevice(
            id=0,
            block_coil=[SimData(...)],
            block_direct=[SimData(...)],
            block_holding=[SimData(...)],
            block_input=[SimData(...)],
        )

    A server can contain either a single :class:`SimDevice` or list of :class:`SimDevice` to simulate a
    multipoint line.
    """

    #: Address of device
    #:
    #: Default 0 means accept all devices, except those defined in the same server.
    #:
    #: .. warning:: A server with a single device id=0 accept all requests.
    id: int = 0

    #: Enforce type checking, if True access are controlled to be conform with datatypes.
    #:
    #: Used to control that read_coils do not access a register defined as holding and visaversa
    type_check: bool = False

    #: Use this block for shared registers (Modern devices).
    #:
    #: Requests accesses all registers in this block.
    #:
    #: .. warning:: cannot be used together with other block_* parameters!
    block_shared: list[SimData] | None = None

    #: Use this block for non-shared registers (very old devices).
    #:
    #: In this block an address is a single coil, there are no registers.
    #:
    #: Request of type read/write_coil accesses this block.
    #:
    #: .. tip:: block_coil/direct/holding/input must all be defined
    block_coil: list[SimData] | None = None

    #: Use this block for non-shared registers (very old devices).
    #:
    #: In this block an address is a single direct relay, there are no registers.
    #:
    #: Request of type read/write_direct_input accesses this block.
    #:
    #: .. tip:: block_coil/direct/holding/input must all be defined
    block_direct: list[SimData] | None = None

    #: Use this block for non-shared registers (very old devices).
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
        if not isinstance(self.id, int) or not 0 <= self.id < 255:
            raise TypeError("0 <= id < 255")
        blocks = [(self.block_shared, "shared")]
        if self.block_shared:
            if self.block_coil or self.block_direct or self.block_holding or self.block_input:
                raise TypeError("block_* cannot be used with block_shared")
        else:
            blocks = [
                (self.block_coil, "coil"),
                (self.block_direct, "direct"),
                (self.block_holding, "holding"),
                (self.block_input, "input")]

        for block, name in blocks:
            if not block:
                raise TypeError(f"block_{name} not defined")
            if not isinstance(block, list):
                raise TypeError(f"block_{name} not a list")
            for entry in block:
                if not isinstance(entry, SimData):
                    raise TypeError(f"block_{name} contains non SimData entries")


def SimCheckConfig(devices: list[SimDevice]) -> bool:
    """Verify configuration."""
    _ = devices
    return False
