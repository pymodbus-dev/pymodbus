"""Simulator device model classes."""
from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeAlias, cast

from ..pdu import ExceptionResponse
from ..pdu.device import ModbusDeviceIdentification
from .simdata import SimData
from .simutils import DataType, SimUtils


SimAction: TypeAlias = Callable[[int, int, list[int], list[int] | None], Awaitable[list[int] | None | ExceptionResponse]]
SimRegs: TypeAlias = tuple[int, list[int], list[int]]
TUPLE_NAMES = (
      "coils",
      "discrete inputs",
      "holding registers",
      "input registers"
   )


@dataclass
class SimDevice:
    """Configure a device with parameters and registers.

    Registers are defined as a list of SimData objects (block).

    Some old devices uses 4 distinct blocks instead of a shared block, to
    support these devices, define the 4 blocks and add them as a set.

    When using distinct blocks, coils and discrete inputs are addressed differently,
    each register represent 1 coil/relay

    **Device with shared registers**::

        SimDevice(
            id=1,
            simdata=[SimData(...)]
        )

    **Device with non-shared registers**::

        SimDevice(
            id=1,
            simdata=([SimData(...)], [SimData(...)], [SimData(...)], [SimData(...)]),
        )

    A server can be configured with either a single :class:`SimDevice` or a list of :class:`SimDevice`
    to simulate a multipoint line.
    """

    #: Address/id of device
    #:
    #: id=0 means all devices, except those specifically defined.
    id: int

    #: List of register blocks (shared registers)
    #: or a tuple with 4 lists of register blocks (non-shared registers)
    #:
    #: The tuple is defined as:
    #:   (<coils>, <discrete inputs>, <holding registers>, <input registers>)
    #:
    #:   <coils> / <discrete inputs> have addressing calculated differently:
    #:       address register = address / 16
    #:       to find the coil at address
    #:       count is number of coils, so registers returned are count +15 / 16.
    #:
    #: ..tip:: addresses not defined are invalid and will produce an ExceptionResponse
    #: ..warning:: lists are sorted on starting address.
    simdata: SimData | list[SimData] | tuple[list[SimData], list[SimData], list[SimData], list[SimData]]

    #: Change endianness.
    #:
    #: Word order is not defined in the modbus standard and thus a device that
    #: uses little-endian is still within the modbus standard.
    #:
    #: Byte order is defined in the modbus standard to be big-endian,
    #: however it is definable to test non-standard modbus devices
    #:
    #: ..tip:: Content (word_order, byte_order), True means big-endian.
    endian: tuple[bool, bool] = (True, True)

    #: String encoding
    #:
    string_encoding: str = "utf-8"

    #: Set device identity
    identity: ModbusDeviceIdentification | None = None

    #: Function to call when registers are being accessed.
    #:
    #: **Example function:**
    #:
    #: .. code-block:: python
    #:
    #:     async def my_action(
    #:         function_code: int,
    #:         start_address: int,
    #:         current_registers: list[int],
    #:         new_registers: list[int] | None) -> list[int] | ExceptionResponse:
    #:
    #:         return registers
    #:          or
    #:         return None
    #:
    #: action, is called with current registers and if write request also the new registers.
    #: result updates registers and if read request returned to the client.
    #:
    #: new_registers is None for read requests.
    #:
    #: if return is None it indicates no change.
    #:
    #: .. tip:: use functools.partial to add extra parameters if needed.
    action: SimAction | None = None

    def __check_simple(self):
        """Check simple parameters."""
        if not isinstance(self.id, int) or not 0 <= self.id <= 255:
            raise TypeError("0 <= id < 255")
        if self.identity and not isinstance(self.identity, ModbusDeviceIdentification):
            raise TypeError("identity= must be a ModbusDeviceIdentification")
        if self.action and not (callable(self.action) and inspect.iscoroutinefunction(self.action)):
            raise TypeError("action= must be a async function")
        if not (isinstance(self.endian, tuple)
            and len(self.endian) == 2
            and isinstance(self.endian[0], bool)
            and isinstance(self.endian[1], bool)
        ):
            raise TypeError("endian= must be a tuple with 2 bool")
        test_str = "test string"
        try:
            test_str.encode(self.string_encoding)
        except (UnicodeEncodeError, LookupError) as exc:
            raise TypeError("string_encoding= not valid") from exc

    def __check_simple2(self):
        """Check simple parameters."""
        if isinstance(self.simdata, SimData):
            self.simdata = [self.simdata]
        if isinstance(self.simdata, list):
            for inx, entry in enumerate(self.simdata):
                if not isinstance(entry, SimData):
                    raise TypeError(f"simdata=list[{inx}] is not a SimData entry")
        else:
            self.__check_simple_blocks()
            if self.action:
                raise TypeError("action= id only supported with shared blocks")

    def __check_simple_blocks(self):
        """Check simple parameters."""
        if not (isinstance(self.simdata, tuple)
                and len(self.simdata) == 4):
            raise TypeError("simdata= must list or tuple")
        for i in range(4):
            sim_list = cast(tuple, self.simdata)[i]
            if not isinstance(sim_list, list):
                raise TypeError(f"simdata=tuple[{TUPLE_NAMES[i]}] -> must be a list")
            for inx, entry in enumerate(sim_list):
                if not isinstance(entry, SimData):
                    raise TypeError(f"simdata[{inx}]=tuple[{TUPLE_NAMES[i]}] -> list[{inx}] is not a SimData entry")
                if i < 2 and entry.datatype != DataType.BITS:
                    raise TypeError(f"simdata[{inx}]=tuple[{TUPLE_NAMES[i]}] -> list[{inx}] not DataType.BITS, not allowed")

    def __check_block(self, block: list[SimData], name: str):
        """Check block content."""
        block.sort(key=lambda x: x.address)
        last_address = block[0].address -1
        for entry in block:
            last_address = self.__check_block_entries(last_address, entry, name)

    def __check_block_entries(self, last_address: int, entry: SimData, _name: str) -> int:
        """Check block entries."""
        if entry.address <= last_address:
            raise TypeError(f"SimData address {entry.address} is overlapping!")
        blocks_regs = entry.build_registers(self.endian, self.string_encoding)
        for registers in blocks_regs:
            last_address += len(registers)
        return last_address

    def __check_parameters(self):
        """Check all parameters."""
        self.__check_simple()
        self.__check_simple2()
        if isinstance(self.simdata, list):
            self.__check_block(self.simdata, "list")
        else:
            for i in range(4):
                self.__check_block(cast(tuple,self.simdata)[i], TUPLE_NAMES[i])

    def __post_init__(self):
        """Define a device."""
        self.__check_parameters()

    def __build_flags(self, simdata: SimData) -> int:
        """Create flags from SimData."""
        flag_normal: int = simdata.datatype
        if simdata.readonly:
            flag_normal |= SimUtils.RunTimeFlag_READONLY
        return flag_normal

    def __create_simdata(self, simdata: SimData, flag_list: list[int],  reg_list: list[int]):
        """Build registers for single SimData."""
        flag_normal  = self.__build_flags(simdata)
        blocks_regs = simdata.build_registers(self.endian, self.string_encoding)
        for registers in blocks_regs:
            first = True
            for reg in registers:
                if first:
                    flag_list.append(flag_normal)
                    first = False
                else:
                    flag_list.append(flag_normal & ~SimUtils.RunTimeFlag_TYPE)
                reg_list.append(reg)

    def __create_block(self, simdata: list[SimData]) -> SimRegs:
        """Create registers for device."""
        flag_list: list[int] = []
        reg_list: list[int] = []
        start_address = simdata[0].address
        for entry in simdata:
            next_address = start_address + len(reg_list)
            while next_address < entry.address:
                flag_list.append(DataType.INVALID)
                reg_list.append(0)
                next_address += 1
            self.__create_simdata(entry, flag_list, reg_list)
        flag_list.append(DataType.INVALID)
        reg_list.append(0)
        return (start_address, reg_list, flag_list)

    def build_device(self) -> SimRegs | dict[str, SimRegs]:
        """Check simdata and built runtime structure."""
        self.__check_parameters()
        if isinstance(self.simdata, list):
            return self.__create_block(self.simdata)
        b: dict[str, SimRegs] = {}
        #  (<coils>, <discrete inputs>, <holding registers>, <input registers>)
        convert = {0: "c", 1: "d", 2: "h", 3: "i"}
        for i in range(4):
            b[convert[i]] = self.__create_block(cast(tuple, self.simdata)[i])
        return b
