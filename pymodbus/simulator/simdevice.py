"""Simulator device model classes."""
from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeAlias, cast

from ..constants import ExcCodes
from ..pdu.device import ModbusDeviceIdentification
from .simdata import SimData
from .simutils import DataType, SimUtils


SimAction: TypeAlias = Callable[[int, int, int, int, list[int], list[int] | list[bool] | None], Awaitable[None | ExcCodes]]
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
    #: ..tip:: addresses not defined are invalid and will produce an ExceptionResponse
    simdata: SimData | list[SimData] | tuple[list[SimData], list[SimData], list[SimData], list[SimData]]

    #: Define coil/discrete input addressing in shared mode.
    #:
    #: False, means the register is addressed, and single bits cannot be addressed.
    #: True, means single bit is being addressed.
    #: effictive address is register_address * 16 + bit_offset.
    #:
    #: Example:
    #:    SimData(200, value=True, datatype=DataType.BITS)
    #: with use_bit_addressing=False:
    #:    read_coils(200) returns [True] + [False] * 7
    #:    read_coils(200, count=16) returns [True] + [False] * 15
    #: with use_bit_addressing=True:
    #:    read_coils(200*16+15) returns [True] + [False] * 7
    #:    read_coils(200*16, count=16) returns [False] * 15 + [True]
    use_bit_addressing: bool | None = None

    #: Set device identity
    identity: ModbusDeviceIdentification | None = None

    #: Function to call when registers are being accessed.
    #:
    #: **Example function:**
    #:
    #: .. code-block:: python
    #:
    #:     async def my_action(
    #:         function_code: int,    # request function code
    #:         start_address: int,    # address of current_registers[0]
    #:         address: int,          # request address
    #:         count: int,            # request count
    #:         current_registers: list[int],  # current registers (modify inline)
    #:         set_values: list[int] | list[bool] | None  # request values to be written (None for read requests)
    #      ) -> None | ExceptionResponse:
    #:
    #: action can:
    #: - update registers (affect the current and future responses)
    #: - update set_values (affect the register update)
    #: - return an ExceptionResponse.
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

    def __check_simple2(self):
        """Check simple parameters."""
        if isinstance(self.simdata, tuple):
            if self.use_bit_addressing is None:
                self.use_bit_addressing = True
            self.__check_simple_blocks()
            if not self.use_bit_addressing:
                raise TypeError("use_bit_addressing=False is only supported with shared blocks")
        else:
            if self.use_bit_addressing is None:
                self.use_bit_addressing = False
            x_simdata = self.simdata if isinstance(self.simdata, list) else [self.simdata]
            for inx, entry in enumerate(x_simdata):
                if not isinstance(entry, SimData):
                    raise TypeError(f"simdata=list[{inx}] is not a SimData entry")

    def __check_simple_blocks(self):
        """Check simple parameters."""
        if not (isinstance(self.simdata, tuple)
                and len(self.simdata) == 4):
            raise TypeError("simdata= must be SimData, list of SimData or tuple with 4 list of SimData")
        for i in range(4):
            sim_list = cast(tuple, self.simdata)[i]
            if not isinstance(sim_list, list):
                raise TypeError(f"simdata=tuple[{TUPLE_NAMES[i]}] -> must be a list")
            for inx, entry in enumerate(sim_list):
                if not isinstance(entry, SimData):
                    raise TypeError(f"simdata[{inx}]=tuple[{TUPLE_NAMES[i]}] -> list[{inx}] is not a SimData entry")
                if i < 2 and entry.datatype != DataType.BITS:
                    raise TypeError(f"simdata[{inx}]=tuple[{TUPLE_NAMES[i]}] -> list[{inx}] not DataType.BITS, not allowed")

    def __check_block(self, block: list[SimData], use_bits, name: str):
        """Check block content."""
        x_block = sorted(block, key=lambda x: x.address)
        last_address = x_block[0].address -1
        for entry in x_block:
            last_address = self.__check_block_entries(last_address, entry, use_bits, name)

    def __check_block_entries(self, last_address: int, entry: SimData, use_bits: bool, _name: str) -> int:
        """Check block entries."""
        if entry.address <= last_address:
            raise TypeError(f"SimData address {entry.address} is overlapping!")
        blocks_regs = entry.build_registers(use_bits) * entry.count
        return last_address + len(blocks_regs)

    def __check_parameters(self):
        """Check all parameters."""
        self.__check_simple()
        self.__check_simple2()
        if isinstance(self.simdata, tuple):
            for i in range(4):
                self.__check_block(cast(tuple,self.simdata)[i], (i in {0,1}), TUPLE_NAMES[i])
        else:
            x_simdata = self.simdata if isinstance(self.simdata, list) else [self.simdata]
            self.__check_block(x_simdata, False, "list")

    def __post_init__(self):
        """Define a device."""
        self.__check_parameters()

    def __build_flags(self, simdata: SimData) -> int:
        """Create flags from SimData."""
        flag_normal: int = simdata.datatype
        if simdata.readonly:
            flag_normal |= SimUtils.RunTimeFlag_READONLY
        return flag_normal

    def __create_simdata(self, simdata: SimData, flag_list: list[int],  reg_list: list[int], use_bits: bool):
        """Build registers for single SimData."""
        flag_normal  = self.__build_flags(simdata)
        blocks_regs = simdata.build_registers(use_bits)
        for _ in range(simdata.count):
            first = True
            for register in blocks_regs:
                if first:
                    flag_list.append(flag_normal)
                    first = False
                else:
                    flag_list.append(flag_normal & ~SimUtils.RunTimeFlag_TYPE)
                reg_list.append(register)

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
            self.__create_simdata(entry, flag_list, reg_list, False)
        flag_list.append(DataType.INVALID)
        reg_list.append(0)
        return (start_address, reg_list, flag_list)

    def __create_block_bits(self, simdata: list[SimData]) -> SimRegs:
        """Create registers for device."""
        bit_list: list[bool] = []
        start_address = simdata[0].address
        if (offset := start_address % 16):
            bit_list.extend([False] * offset)
            start_address -= offset
        for entry in simdata:
            if (next_address := start_address + len(bit_list)) < entry.address:
                bit_list.extend([False] * (entry.address - next_address))
                next_address = start_address + len(bit_list)
            entry_bits = entry.build_registers(True)
            bit_list.extend(cast(list[bool], entry_bits))
        if (remains := len(bit_list) % 16):
            bit_list.extend([False] * (16 - remains))

        flag_list: list[int] = [DataType.BITS] + [0] * (int(len(bit_list) / 16) -1) + [DataType.INVALID]
        bit_list.extend([False] * (len(bit_list) % 16))
        reg_list = SimUtils.bitsToRegisters(bit_list)
        reg_list.append(0)
        return (int(start_address / 16), reg_list, flag_list)

    def build_device(self) -> SimRegs | dict[str, SimRegs]:
        """Check simdata and built runtime structure."""
        self.__check_parameters()
        if not isinstance(self.simdata, tuple):
            x_simdata = self.simdata if isinstance(self.simdata, list) else [self.simdata]
            x_simdata.sort(key=lambda x: x.address)
            return self.__create_block(x_simdata)
        b: dict[str, SimRegs] = {}
        #  (<coils>, <discrete inputs>, <holding registers>, <input registers>)
        convert = {0: "c", 1: "d", 2: "h", 3: "i"}
        for i in range(4):
            x_simdata = cast(tuple, self.simdata)[i]
            x_simdata.sort(key=lambda x: x.address)
            if i in {0,1}:
                b[convert[i]] = self.__create_block_bits(x_simdata)
            else:
                b[convert[i]] = self.__create_block(x_simdata)
        return b
