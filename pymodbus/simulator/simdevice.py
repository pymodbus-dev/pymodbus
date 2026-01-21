"""Simulator device model classes.

**REMARK** This code is experimental and not integrated into production.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from pymodbus.constants import DATATYPE_STRUCT, DataType

from .simdata import SimData


@dataclass(order=True, frozen=True)
class SimDevice:
    """Configure a device with parameters and registers.

    Registers are always defined as one block.

    Some old devices uses 4 distinct blocks instead of 1 block, to
    support these devices, define 1 large block consisting of the
    4 blocks and use the offset_*= parameters.

    When using distinct blocks, coils and discrete inputs are addressed differently,
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
            offset_discrete=10,
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

    #: Default SimData to be used for registers not defined.
    default: SimData | None = None

    #: Define starting address for each of the 4 blocks.
    #:
    #: .. tip:: Content (coil, discrete, holding, input) in growing order.
    offset_address: tuple[int, int, int, int] | None = None

    #: Enforce type checking, if True access are controlled to be conform with datatypes.
    #:
    #: Type violations like e.g. reading INT32 as INT16 are returned as ExceptionResponses,
    #: as well as being logged.
    type_check: bool = False

    #: Change endianness.
    #:
    #: Word order is not defined in the modbus standard and thus a device that
    #: uses little-endian is still within the modbus standard.
    #:
    #: Byte order is defined in the modbus standard to be big-endian,
    #: however it is definable to test non-standard modbus devices
    #:
    #: ..tip:: Content (word_order, byte_order)
    endian: tuple[bool, bool] = (True, True)

    #: Set device identity
    #:
    identity: str = "pymodbus simulator/server"


    def __check_block(self, block: list[SimData]) -> list[SimData]:
        """Check block content."""
        if not block:
            return block
        for inx, entry in enumerate(block):
            if not isinstance(entry, SimData):
                raise TypeError(f"registers[{inx}]= is a SimData entry")
        block.sort(key=lambda x: x.address)
        last_address = -1
        for entry in block:
            last_address = self.__check_block_entries(last_address, entry)
        if self.default and block:
            first_address = block[0].address
            if self.default.address > first_address:
                raise TypeError("Default address is {self.default.address} but {first_address} is defined?")
            def_last_address = self.default.address + self.default.count -1
            if last_address > def_last_address:
                raise TypeError("Default address+count is {def_last_address} but {last_address} is defined?")
        return block

    def __check_block_entries(self, last_address: int, entry: SimData) -> int:
        """Check block entries."""
        values = entry.values if isinstance(entry.values, list) else [entry.values]
        if entry.address <= last_address:
            raise TypeError("SimData address {entry.address} is overlapping!")
        if entry.datatype == DataType.BITS:
            if isinstance(values[0], bool):
                reg_count = int((len(values) + 15) / 16)
            else:
                reg_count = len(values)
            return entry.address + reg_count * entry.count -1
        if entry.datatype == DataType.STRING:
            return entry.address + len(cast(str, entry.values)) * entry.count -1
        register_count = DATATYPE_STRUCT[entry.datatype][1]
        return entry.address + register_count * entry.count -1

    def __check_simple(self):
        """Check simple parameters."""
        if not isinstance(self.id, int) or not 0 <= self.id <= 255:
            raise TypeError("0 <= id < 255")
        if not isinstance(self.registers, list):
            raise TypeError("registers= not a list")
        if not self.default and not self.registers:
            raise TypeError("Either registers= or default= must contain SimData")
        if not isinstance(self.type_check, bool):
            raise TypeError("type_check= not a bool")
        if (not self.endian
            or not isinstance(self.endian, tuple)
            or len(self.endian) != 2
            or not isinstance(self.endian[0], bool)
            or not isinstance(self.endian[1], bool)
        ):
            raise TypeError("endian= must be a tuple with 2 bool")
        if not isinstance(self.identity, str):
            raise TypeError("identity= must be a string")
        if not self.default:
            return
        if not isinstance(self.default, SimData):
            raise TypeError("default= must be a SimData object")
        if not self.default.datatype == DataType.REGISTERS:
            raise TypeError("default= only allow datatype=DataType.REGISTERS")

    def __post_init__(self):
        """Define a device."""
        self.__check_simple()
        super().__setattr__("registers", self.__check_block(self.registers))
        if self.offset_address is not None:
            if not isinstance(self.offset_address, tuple):
                raise TypeError("offset_address= must be a tuple")
            if len(self.offset_address) != 4:
                raise TypeError("offset_address= must be a tuple with 4 addresses")
            if self.default:
                reg_start = self.default.address
                reg_end = self.default.address + self.default.count -1
            else:
                reg_start = self.registers[0].address
                reg_end = self.registers[-1].address
            for i in range(4):
                if not (reg_start < self.offset_address[i] < reg_end):
                    raise TypeError(f"offset_address[{i}] outside defined range")
                if i and self.offset_address[i-1] >= self.offset_address[i]:
                    raise TypeError("offset_address= must be ascending addresses")

@dataclass(order=True, frozen=True)
class SimDevices:
    """Define a group of devices.

    If wanting to use multiple devices in a single server,
    each SimDevice must be grouped with SimDevices.
    """

    #: Add a list of SimDevice
    devices: list[SimDevice]

    def __post_init__(self):
        """Define a group of devices."""
        if not isinstance(self.devices, list):
            raise TypeError("devices= must be a list of SimDevice")
        if not self.devices:
            raise TypeError("devices= must contain at least 1 SimDevice")
        list_id = []
        for device in self.devices:
            if not isinstance(device, SimDevice):
                raise TypeError("devices= contains non SimDevice entries")
            if device.id in list_id:
                raise TypeError(f"device_id={device.id} is duplicated")
            list_id.append(device.id)
