"""Pymodbus ModbusSimulatorContext."""
from __future__ import annotations

import dataclasses
import random
import struct
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pymodbus.datastore.context import ModbusBaseSlaveContext


WORD_SIZE = 16


@dataclasses.dataclass(frozen=True)
class CellType:
    """Define single cell types."""

    INVALID: int = 0
    BITFIELD16: int = 1
    BITFIELD32: int = 2
    BITFIELD64: int = 3
    INT16: int = 4
    INT32: int = 5
    INT64: int = 6
    UINT16: int = 7
    UINT32: int = 8
    UINT64: int = 9
    FLOAT32: int = 10
    FLOAT64: int = 11
    STRING: int = 12
    NEXT: int = 13


@dataclasses.dataclass(repr=False, eq=False)
class Cell:
    """Handle a single cell."""

    type: int = CellType.INVALID
    access: bool = False
    value: int = 0
    action: int = 0
    action_kwargs: dict[str, Any] | None = None
    count_read: int = 0
    count_write: int = 0


class TextCell:  # pylint: disable=too-few-public-methods
    """A textual representation of a single cell."""

    type: str
    access: str
    value: str
    action: str
    action_kwargs: str
    count_read: str
    count_write: str


@dataclasses.dataclass
class Label:  # pylint: disable=too-many-instance-attributes
    """Defines all dict values.

    :meta private:
    """

    action: str = "action"
    addr: str = "addr"
    any: str = "any"
    co_size: str = "co size"
    defaults: str = "defaults"
    di_size: str = "di size"
    hr_size: str = "hr size"
    increment: str = "increment"
    invalid: str = "invalid"
    ir_size: str = "ir size"
    kwargs: str = "kwargs"
    method: str = "method"
    next: str = "next"
    none: str = "none"
    random: str = "random"
    repeat: str = "repeat"
    reset: str = "reset"
    setup: str = "setup"
    shared_blocks: str = "shared blocks"
    timestamp: str = "timestamp"
    repeat_to: str = "to"
    type: str = "type"
    type_bitfield16 = "bitfield16"
    type_bitfield32 = "bitfield32"
    type_bitfield64 = "bitfield64"
    type_exception: str = "type exception"
    type_int16: str = "int16"
    type_int32: str = "int32"
    type_int64: str = "int64"
    type_uint16: str = "uint16"
    type_uint32: str = "uint32"
    type_uint64: str = "uint64"
    type_float32: str = "float32"
    type_float64: str = "float64"
    type_string: str = "string"
    uptime: str = "uptime"
    value: str = "value"
    write: str = "write"

    @classmethod
    def try_get(cls, key, config_part):
        """Check if entry is present in config."""
        if key not in config_part:
            txt = f"ERROR Configuration invalid, missing {key} in {config_part}"
            raise RuntimeError(txt)
        return config_part[key]


class Setup:
    """Setup simulator.

    :meta private:
    """

    def __init__(self, runtime):
        """Initialize."""
        self.runtime = runtime
        self.config = {}
        self.config_types: dict[str, dict[str, Any]] = {
            Label.type_bitfield16: {
                Label.type: CellType.BITFIELD16,
                Label.next: None,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_bitfield16,
            },
            Label.type_bitfield32: {
                Label.type: CellType.BITFIELD32,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_bitfield32,
            },
            Label.type_bitfield64: {
                Label.type: CellType.BITFIELD64,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_bitfield64,
            },
             Label.type_int16: {
                Label.type: CellType.INT16,
                Label.next: None,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_int16,
            },
            Label.type_int32: {
                Label.type: CellType.INT32,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_int32,
            },
            Label.type_int64: {
                Label.type: CellType.INT64,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_int64,
            },
            Label.type_uint16: {
                Label.type: CellType.UINT16,
                Label.next: None,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_uint16,
            },
            Label.type_uint32: {
                Label.type: CellType.UINT32,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_uint32,
            },
            Label.type_uint64: {
                Label.type: CellType.UINT64,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_uint64,
            },
            Label.type_float32: {
                Label.type: CellType.FLOAT32,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_float32,
            },
            Label.type_float64: {
                Label.type: CellType.FLOAT64,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_float64,
            }, 
            Label.type_string: {
                Label.type: CellType.STRING,
                Label.next: CellType.NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_string,
            },
        }

    def handle_type_2Bytes(self, start, stop, regs_value, action, action_kwargs,cell_type):
        """Handle datatypes that require 2 bytes in order to be represented, e.g., 1 register"""
        for i in range(start, stop, 1):
            regs = self.runtime.registers[i : i+1]
            assert len(regs)==1,"Failed assertion"
            if regs[0].type != CellType.INVALID :
                raise RuntimeError(f'ERROR "{cell_type}" {i}  is already being used')
       
            regs[0].action = action
            regs[0].action_kwargs = action_kwargs
            for ix in range (0,1):
                regs[ix].value = regs_value[ix]
                regs[ix].type = CellType.NEXT   #Reg0 will be rewritten next
            regs[0].type = cell_type

    def handle_type_4Bytes(self, start, stop, regs_value, action, action_kwargs,cell_type):
         """Handle datatypes that require 4 bytes in order to be represented, e.g., 2 registers"""
         for i in range(start, stop, 2):
            regs = self.runtime.registers[i : i + 2]
            if regs[0].type != CellType.INVALID or regs[1].type != CellType.INVALID:
                raise RuntimeError(f'ERROR "{cell_type}" {i},{i + 1} is already being used')
       
            regs[0].action = action
            regs[0].action_kwargs = action_kwargs
            for ix in range (0,2):
                regs[ix].value = regs_value[ix]
                regs[ix].type = CellType.NEXT   #Reg0 will be rewritten next
            regs[0].type = cell_type

    def handle_type_8Bytes(self, start, stop, regs_value, action, action_kwargs,cell_type):
        """Handle datatypes that require 8 bytes in order to be represented, e.g., 4 registers"""
        for i in range(start, stop, 4):
            regs = self.runtime.registers[i : i + 4]
            if regs[0].type != CellType.INVALID or regs[1].type != CellType.INVALID or regs[2].type != CellType.INVALID or regs[3].type != CellType.INVALID:
                raise RuntimeError(f'ERROR "{cell_type}" {i},{i + 1},{i + 2},{i + 3} is already being used')
            regs[0].action = action
            regs[0].action_kwargs = action_kwargs
            for ix in range (0,4):
                regs[ix].value = regs_value[ix]
                regs[ix].type = CellType.NEXT   #Reg0 will be rewritten next
            regs[0].type = cell_type
    def handle_type_bitfield16(self, start, stop, value, action, action_kwargs):
        """Handle type bits.16"""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,2,False)
        self.handle_type_2Bytes( start, stop, regs_value, action, action_kwargs,CellType.BITFIELD16)
    def handle_type_bitfield32(self, start, stop, value, action, action_kwargs):
        """Handle type bits.32"""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,4,False)
        self.handle_type_4Bytes( start, stop, regs_value, action, action_kwargs,CellType.BITFIELD32)
    def handle_type_bitfield64(self, start, stop, value, action, action_kwargs):
        """Handle type bits.64"""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,8,False)
        self.handle_type_8Bytes( start, stop, regs_value, action, action_kwargs,CellType.BITFIELD64)

    def handle_type_int16(self, start, stop, value, action, action_kwargs):
        """Handle type int16."""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,2,True)
        self.handle_type_2Bytes( start, stop, regs_value, action, action_kwargs,CellType.INT16)

    def handle_type_int32(self, start, stop, value, action, action_kwargs):
        """Handle type int32."""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,4,True)
        self.handle_type_4Bytes( start, stop, regs_value, action, action_kwargs,CellType.INT32)
       
    def handle_type_int64(self, start, stop, value, action, action_kwargs):
        """Handle type int64."""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,8,True)
        self.handle_type_8Bytes( start, stop, regs_value, action, action_kwargs,CellType.INT64)
       
    def handle_type_uint16(self, start, stop, value, action, action_kwargs):
        """Handle type uint16."""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,2,False)
        self.handle_type_2Bytes( start, stop, regs_value, action, action_kwargs,CellType.UINT16)

    def handle_type_uint32(self, start, stop, value, action, action_kwargs):
        """Handle type uint32."""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,4,False)
        self.handle_type_4Bytes( start, stop, regs_value, action, action_kwargs,CellType.UINT32)
            
    def handle_type_uint64(self, start, stop, value, action, action_kwargs):
        """Handle type uint64."""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, True,8,False)
        self.handle_type_8Bytes( start, stop, regs_value, action, action_kwargs,CellType.UINT64)

    def handle_type_float32(self, start, stop, value, action, action_kwargs):
        """Handle type uint32."""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, False,4,None)
        self.handle_type_4Bytes( start, stop, regs_value, action, action_kwargs,CellType.FLOAT32)

    def handle_type_float64(self, start, stop, value, action, action_kwargs):
        """Handle type float64."""
        regs_value = ModbusSimulatorContext.build_registers_from_value(value, False,8,None)
        self.handle_type_8Bytes( start, stop, regs_value, action, action_kwargs,CellType.FLOAT64)

    def handle_type_string(self, start, stop, value, action, action_kwargs):
        """Handle type string."""
        regs = stop - start
        reg_len = regs * 2
        if len(value) > reg_len:
            raise RuntimeError(
                f'ERROR "{Label.type_string}" {start} too long "{value}"'
            )
        value = value.ljust(reg_len)
        for i in range(stop - start):
            reg = self.runtime.registers[start + i]
            if reg.type != CellType.INVALID:
                raise RuntimeError(f'ERROR "{Label.type_string}" at location {start + i} is already being used')
            j = i * 2
            reg.value = int.from_bytes(bytes(value[j : j + 2], "UTF-8"), "big")
            reg.type = CellType.NEXT
        self.runtime.registers[start].type = CellType.STRING
        self.runtime.registers[start].action = action
        self.runtime.registers[start].action_kwargs = action_kwargs

    def handle_setup_section(self):
        """Load setup section."""
        layout = Label.try_get(Label.setup, self.config)
        self.runtime.fc_offset = {key: 0 for key in range(25)}
        size_co = Label.try_get(Label.co_size, layout)
        size_di = Label.try_get(Label.di_size, layout)
        size_hr = Label.try_get(Label.hr_size, layout)
        size_ir = Label.try_get(Label.ir_size, layout)
        if Label.try_get(Label.shared_blocks, layout):
            total_size = max(size_co, size_di, size_hr, size_ir)
        else:
            # set offset (block) for each function code
            # starting with fc = 1, 5, 15
            self.runtime.fc_offset[2] = size_co
            total_size = size_co + size_di
            self.runtime.fc_offset[4] = total_size
            total_size += size_ir
            for i in (3, 6, 16, 22, 23):
                self.runtime.fc_offset[i] = total_size
            total_size += size_hr
        first_cell = Cell()
        self.runtime.registers = [
            dataclasses.replace(first_cell) for i in range(total_size)
        ]
        self.runtime.register_count = total_size
        self.runtime.type_exception = bool(Label.try_get(Label.type_exception, layout))
        defaults = Label.try_get(Label.defaults, layout)
        defaults_value = Label.try_get(Label.value, defaults)
        defaults_action = Label.try_get(Label.action, defaults)
        for key, entry in self.config_types.items():
            entry[Label.value] = Label.try_get(key, defaults_value)
            if (
                action := Label.try_get(key, defaults_action)
            ) not in self.runtime.action_name_to_id:
                raise RuntimeError(f"ERROR illegal action {key} in {defaults_action}")
            entry[Label.action] = action
        del self.config[Label.setup]

    def handle_invalid_address(self):
        """Handle invalid address."""
        for entry in Label.try_get(Label.invalid, self.config):
            if isinstance(entry, int):
                entry = [entry, entry]
            for i in range(entry[0], entry[1] + 1):
                if i >= self.runtime.register_count:
                    raise RuntimeError(
                        f'Error section "{Label.invalid}" addr {entry} out of range'
                    )
                reg = self.runtime.registers[i]
                reg.type = CellType.INVALID
        del self.config[Label.invalid]

    def handle_write_allowed(self):
        """Handle write allowed."""
        for entry in Label.try_get(Label.write, self.config):
            if isinstance(entry, int):
                entry = [entry, entry]
            for i in range(entry[0], entry[1] + 1):
                if i >= self.runtime.register_count:
                    raise RuntimeError(
                        f'Error section "{Label.write}" addr {entry} out of range'
                    )
                reg = self.runtime.registers[i]
                if reg.type == CellType.INVALID:
                    txt = f'ERROR Configuration invalid in section "write" register {i} not defined'
                    raise RuntimeError(txt)
                reg.access = True
        del self.config[Label.write]

    def handle_types(self):
        """Handle the different types."""
        for section, type_entry in self.config_types.items():
            layout = Label.try_get(section, self.config)
            for entry in layout:
                if not isinstance(entry, dict):
                    entry = {Label.addr: entry}
                regs = Label.try_get(Label.addr, entry)
                if not isinstance(regs, list):
                    regs = [regs, regs]
                start = regs[0]
                if (stop := regs[1]) >= self.runtime.register_count:
                    raise RuntimeError(f'Error "{section}" {start}, {stop} illegal')
                type_entry[Label.method](
                    start,
                    stop + 1,
                    entry.get(Label.value, type_entry[Label.value]),
                    self.runtime.action_name_to_id[
                        entry.get(Label.action, type_entry[Label.action])
                    ],
                    entry.get(Label.kwargs, None),
                )
            del self.config[section]

    def handle_repeat(self):
        """Handle repeat."""
        for entry in Label.try_get(Label.repeat, self.config):
            addr = Label.try_get(Label.addr, entry)
            copy_start = addr[0]
            copy_end = addr[1]
            copy_inx = copy_start - 1
            addr_to = Label.try_get(Label.repeat_to, entry)
            for inx in range(addr_to[0], addr_to[1] + 1):
                copy_inx = copy_start if copy_inx >= copy_end else copy_inx + 1
                if inx >= self.runtime.register_count:
                    raise RuntimeError(
                        f'Error section "{Label.repeat}" entry {entry} out of range'
                    )
                self.runtime.registers[inx] = dataclasses.replace(
                    self.runtime.registers[copy_inx]
                )
        del self.config[Label.repeat]

    def setup(self, config, custom_actions) -> None:
        """Load layout from dict with json structure."""
        actions = {
            Label.increment: self.runtime.action_increment,
            Label.random: self.runtime.action_random,
            Label.reset: self.runtime.action_reset,
            Label.timestamp: self.runtime.action_timestamp,
            Label.uptime: self.runtime.action_uptime,
        }
        if custom_actions:
            actions.update(custom_actions)
        self.runtime.action_name_to_id = {None: 0}
        self.runtime.action_id_to_name = [Label.none]
        self.runtime.action_methods = [None]
        i = 1
        for key, method in actions.items():
            self.runtime.action_name_to_id[key] = i
            self.runtime.action_id_to_name.append(key)
            self.runtime.action_methods.append(method)
            i += 1
        self.runtime.registerType_name_to_id = {
            Label.type_bitfield16: CellType.BITFIELD16,
            Label.type_bitfield32: CellType.BITFIELD32,
            Label.type_bitfield64: CellType.BITFIELD64,
            Label.type_int16: CellType.INT16,
            Label.type_int32: CellType.INT32,
            Label.type_int64: CellType.INT64,
            Label.type_uint16: CellType.UINT16,
            Label.type_uint32: CellType.UINT32,
            Label.type_uint64: CellType.UINT64,
            Label.type_float32: CellType.FLOAT32,
            Label.type_float64: CellType.FLOAT64,
            Label.type_string: CellType.STRING,
            Label.next: CellType.NEXT,
            Label.invalid: CellType.INVALID,
        }
        self.runtime.registerType_id_to_name = [None] * len(
            self.runtime.registerType_name_to_id
        )
        for name, cell_type in self.runtime.registerType_name_to_id.items():
            self.runtime.registerType_id_to_name[cell_type] = name

        self.config = config
        self.handle_setup_section()
        self.handle_invalid_address()
        self.handle_types()
        self.handle_write_allowed()
        self.handle_repeat()
        if self.config:
            raise RuntimeError(f"INVALID key in setup: {self.config}")


class ModbusSimulatorContext(ModbusBaseSlaveContext):
    """Modbus simulator.

    :param config: A dict with structure as shown below.
    :param actions: A dict with "<name>": <function> structure.
    :raises RuntimeError: if json contains errors (msg explains what)

    It builds and maintains a virtual copy of a device, with simulation of
    device specific functions.

    The device is described in a dict, user supplied actions will
    be added to the builtin actions.

    It is used in conjunction with a pymodbus server.

    Example::

        store = ModbusSimulatorContext(<config dict>, <actions dict>)
        StartAsyncTcpServer(<host>, context=store)

        Now the server will simulate the defined device with features like:

        - invalid addresses
        - write protected addresses
        - optional control of access for string, uint32, bit/bits
        - builtin actions for e.g. reset/datetime, value increment by read
        - custom actions

    Description of the json file or dict to be supplied::

        {
            "setup": {
                "di size": 0,  --> Size of discrete input block (8 bit)
                "co size": 0,  --> Size of coils block (8 bit)
                "ir size": 0,  --> Size of input registers block (16 bit)
                "hr size": 0,  --> Size of holding registers block (16 bit)
                "shared blocks": True,  --> share memory for all blocks (largest size wins)
                "defaults": {
                    "value": {  --> Initial values (can be overwritten)
                        "bitfield16": 0x0001,  -> e.g., a 16-bitmask
                        "bitfield32": 0x00010000,-> e.g., a 32-bitmask
                        "bitfield64": 0x0000000100000000,-> e.g., a 64-bitmask
                        "int16": -16,
                        "int32": -32,
                        "int64": -64,
                        "uint16": 122,
                        "uint32": 67000,
                        "uint64": 67000,
                        "float32": 127.4,
                        "float64": 127.4,
                        "string": " ",
                    },
                    "action": {  --> default action (can be overwritten)
                        "bitfield16": None,
                        "bitfield32": None,
                        "bitfield64": None,
                        "int16": None,
                        "int32": None,
                        "int64": None,
                        "uint16": None,
                        "uint32": None,
                        "uint64": None,
                        "float32": None,
                        "string": None,
                    },
                },
                "type exception": False,  --> return IO exception if read/write on non boundary
            },
            "invalid": [  --> List of invalid addresses, IO exception returned
                51,                --> single register
                [78, 99],         --> start, end registers, repeated as needed
            ],
            "write": [   --> allow write, efault is ReadOnly
                [5, 5]  --> start, end bytes, repeated as needed
            ],
            "bitfield16": [  --> Define bits (1 register == 2 bytes)
                [30, 30],  --> start, end registers,
                {"addr": [32, 32], "value": 0xF1},  --> with value
                {"addr": [35, 35], "action": "increment"},  --> with action
                {"addr": [37, 37], "action": "increment", "value": 0xF1}  --> with action and value
                {"addr": [37, 37], "action": "increment", "kwargs": {"min": 0, "max": 100}}  --> with action with arguments
            ],
            "int16": [  --> Define int16,signed (1 register == 2 bytes)
                --> similar to bitfield16, but intended to represent a  16bit SIGNED number (-32768 <-> 32767)
            ],
            "int32": [  --> Define 32 bit signed integers (2 registers == 4 bytes)
                --> similar to int16, but intended to represent a  32bit SIGNED number, occupies 2 registers
                {'addr': [88, 89], 'value': 32}
            ],
            "int64": [  --> Define 64 bit signed integers (4 registers == 8 bytes)
                --> similar to int32,  uses 4 registers
                {'addr': [88, 91], 'value': 64}
            ],
            "uint16": [  --> Define uint16 (1 register == 2 bytes)
                --> similar to int16, unsigned
            ],
            "uint32": [  --> Define 32 bit unsigned integers (2 registers == 4 bytes)
                --> similar to int32, unsigned
            ],
            "uint64": [  --> Define 32 bit unsigned integers (4 registers == 8 bytes)
                --> similar to int64, unsigned
            ],
            "float32": [  --> Define 32 bit floats (2 registers == 4 bytes)
                --> similar to int32, but encoding a floating number
            ],
            "float64": [  --> Define 64 bit floats (4 registers == 4 bytes)
                -->  similar to int32, but encoding a floating number
            ],
            "string": [  --> Define strings (variable number of registers (each 2 bytes))
                [21, 22],  --> start, end registers, define 1 string
                {"addr": 23, 25], "value": "ups"},  --> with value
                {"addr": 26, 27], "action": "user"},  --> with action
                {"addr": 28, 29], "action": "", "value": "user"}  --> with action and value
            ],
            "repeat": [ --> allows to repeat section e.g. for n devices
                {"addr": [100, 200], "to": [50, 275]}   --> Repeat registers 100-200 to 50+ until 275
            ]
        }
    """

    # --------------------------------------------
    # External interfaces
    # --------------------------------------------
    start_time = int(datetime.now().timestamp())

    def __init__(
        self, config: dict[str, Any], custom_actions: dict[str, Callable] | None
    ) -> None:
        """Initialize."""
        self.registers: list[Cell] = []
        self.fc_offset: dict[int, int] = {}
        self.register_count = 0
        self.type_exception = False
        self.action_name_to_id: dict[str, int] = {}
        self.action_id_to_name: list[str] = []
        self.action_methods: list[Callable] = []
        self.registerType_name_to_id: dict[str, int] = {}
        self.registerType_id_to_name: list[str] = []
        Setup(self).setup(config, custom_actions)

    # --------------------------------------------
    # Simulator server interface
    # --------------------------------------------
    def get_text_register(self, register):
        """Get raw register."""
        reg = self.registers[register]
        text_cell = TextCell()
        text_cell.type = self.registerType_id_to_name[reg.type]
        text_cell.access = str(reg.access)
        text_cell.count_read = str(reg.count_read)
        text_cell.count_write = str(reg.count_write)
        text_cell.action = self.action_id_to_name[reg.action]
        if reg.action_kwargs:
            text_cell.action = f"{text_cell.action}({reg.action_kwargs})"
        if reg.type in (CellType.INVALID, CellType.NEXT):
            text_cell.value = str(reg.value)
            build_len = 0
        elif reg.type == CellType.BITFIELD16:
            tmp_regs = [reg.value]
            value=self.build_value_from_registers(tmp_regs, True,2,False)
            text_cell.value ='0x' + hex(value)[2:].zfill(4) 
            build_len = 0
        elif reg.type == CellType.BITFIELD32:
            tmp_regs = [reg.value, self.registers[register + 1].value]
            value=self.build_value_from_registers(tmp_regs, True,4,False)
            text_cell.value ='0x' + hex(value)[2:].zfill(8) 
            build_len = 2
        elif reg.type == CellType.BITFIELD64:
            tmp_regs = [reg.value, self.registers[register + 1].value, self.registers[register + 2].value, self.registers[register + 3].value]
            value=self.build_value_from_registers(tmp_regs, True,8,False)
            text_cell.value ='0x' + hex(value)[2:].zfill(16) 
            build_len = 3
        elif reg.type in (CellType.UINT16,CellType.INT16):
            tmp_regs = [reg.value, self.registers[register + 1].value]
            is_signed= bool( reg.type ==CellType.INT16 )
            text_cell.value = str(self.build_value_from_registers(tmp_regs, True,2,is_signed))
            build_len = 1
        elif reg.type in (CellType.UINT32,CellType.INT32):
            tmp_regs = [reg.value, self.registers[register + 1].value]
            is_signed=bool( reg.type ==CellType.INT32 )
            text_cell.value = str(self.build_value_from_registers(tmp_regs, True,4,is_signed))
            build_len = 1
        elif reg.type in (CellType.UINT64,CellType.INT64):
            tmp_regs = [reg.value, self.registers[register + 1].value,self.registers[register + 2].value, self.registers[register + 3].value]
            is_signed=bool( reg.type ==CellType.INT64 )
            text_cell.value = str(self.build_value_from_registers(tmp_regs, True,8,is_signed))
            build_len = 1
        elif reg.type == CellType.FLOAT32:
            tmp_regs = [reg.value, self.registers[register + 1].value]
            text_cell.value = str(self.build_value_from_registers(tmp_regs, False,4,None))
            build_len = 1
        elif reg.type == CellType.FLOAT64:
            tmp_regs = [reg.value, self.registers[register + 1].value, self.registers[register + 2].value, self.registers[register + 3].value]
            text_cell.value = str(self.build_value_from_registers(tmp_regs, False,8,None))
            build_len = 3
        elif reg.type == CellType.STRING:
            j = register
            text_cell.value = ""
            while True:
                text_cell.value += str(
                    self.registers[j].value.to_bytes(2, "big"),
                    encoding="utf-8",
                    errors="ignore",
                )
                j += 1
                if self.registers[j].type != CellType.NEXT:
                    break
            build_len = j - register - 1
        else:
            #Make sure all data types have a custom text generator, otherwise raise an error
            assert 1==2,"There is no text representation for the input type"
        reg_txt = f"{register}-{register + build_len}" if build_len else f"{register}"
        return reg_txt, text_cell

    # --------------------------------------------
    # Modbus server interface
    # --------------------------------------------

    _write_func_code = (5, 6, 15, 16, 22, 23)
    _bits_func_code = (1, 2, 5, 15)

    def loop_validate(self, address, end_address, fx_write):
        """Validate entry in loop.

        :meta private:
        """
        i = address
        while i < end_address:
            reg = self.registers[i]
            if fx_write and not reg.access or reg.type == CellType.INVALID:
                return False
            if not self.type_exception:
                i += 1
                continue
            if reg.type == CellType.NEXT:
                return False
            if reg.type in (CellType.BITFIELD16, CellType.UINT16,CellType.INT16):
                i += 1
            elif reg.type in (CellType.BITFIELD32,CellType.UINT32,CellType.INT32, CellType.FLOAT32):
                if i + 1 >= end_address:
                    return False
                i += 2
            elif reg.type in (CellType.BITFIELD64,CellType.UINT64,CellType.INT64, CellType.FLOAT64):
                if i + 3 >= end_address:
                    return False
                i += 4
            elif reg.type == CellType.STRING:
                i += 1
                while i < end_address:
                    if self.registers[i].type == CellType.NEXT:
                        i += 1
                    else:
                        break
            else:
                assert 1==2, "A cell without validation handler has been found"
                return False
        return True

    def validate(self, func_code, address, count=1):
        """Check to see if the request is in range.

        :meta private:
        """
        if func_code in self._bits_func_code:
            # Bit count, correct to register count
            count = int((count + WORD_SIZE - 1) / WORD_SIZE)
            address = int(address / 16)

        real_address = self.fc_offset[func_code] + address
        if real_address < 0 or real_address > self.register_count:
            return False

        fx_write = func_code in self._write_func_code
        return self.loop_validate(real_address, real_address + count, fx_write)

    def getValues(self, func_code, address, count=1):
        """Return the requested values of the datastore.

        :meta private:
        """
        result = []
        if func_code not in self._bits_func_code:
            real_address = self.fc_offset[func_code] + address
            for i in range(real_address, real_address + count):
                reg = self.registers[i]
                kwargs = reg.action_kwargs if reg.action_kwargs else {}
                if reg.action:
                    self.action_methods[reg.action](self.registers, i, reg, **kwargs)
                self.registers[i].count_read += 1
                result.append(reg.value)
        else:
            # bit access
            real_address = self.fc_offset[func_code] + int(address / 16)
            bit_index = address % 16
            reg_count = int((count + bit_index + 15) / 16)
            for i in range(real_address, real_address + reg_count):
                reg = self.registers[i]
                if reg.action:
                    kwargs = reg.action_kwargs or {}
                    self.action_methods[reg.action](
                        self.registers, i, reg, **kwargs
                    )
                self.registers[i].count_read += 1
                while count and bit_index < 16:
                    result.append(bool(reg.value & (2**bit_index)))
                    count -= 1
                    bit_index += 1
                bit_index = 0
        return result

    def setValues(self, func_code, address, values):
        """Set the requested values of the datastore.

        :meta private:
        """
        if func_code not in self._bits_func_code:
            real_address = self.fc_offset[func_code] + address
            for value in values:
                self.registers[real_address].value = value
                self.registers[real_address].count_write += 1
                real_address += 1
            return

        # bit access
        real_address = self.fc_offset[func_code] + int(address / 16)
        bit_index = address % 16
        for value in values:
            bit_mask = 2**bit_index
            if bool(value):
                self.registers[real_address].value |= bit_mask
            else:
                self.registers[real_address].value &= ~bit_mask
            self.registers[real_address].count_write += 1
            bit_index += 1
            if bit_index == 16:
                bit_index = 0
                real_address += 1
        return

    # --------------------------------------------
    # Internal action methods
    # --------------------------------------------

    @classmethod
    def action_random(cls, registers, inx, cell, minval=1, maxval=65536):
        """Update with random value.

        :meta private:
        """


        if cell.type in (CellType.BITFIELD16, CellType.INT16, CellType.UINT16):
            is_signed=bool( CellType.INT16)
            registers[inx].value = random.randint(int(minval), int(maxval))
        elif cell.type in (CellType.BITFIELD32, CellType.INT32, CellType.UINT32):
            is_signed=bool( CellType.INT32)
            regs = cls.build_registers_from_value(
                random.randint(int(minval), int(maxval)),True,4,is_signed
            )
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type in (CellType.BITFIELD64, CellType.INT64, CellType.UINT64):
            is_signed=bool( CellType.INT64)
            regs = cls.build_registers_from_value(
                random.randint(int(minval), int(maxval)),True,8,is_signed
            )
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
            registers[inx + 2].value = regs[2]
            registers[inx + 3].value = regs[3]
        elif cell.type == CellType.FLOAT32:
            regs = cls.build_registers_from_value(
                random.uniform(float(minval), float(maxval)),False,4 ,None
            )
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type == CellType.FLOAT64:
            regs = cls.build_registers_from_value(
                random.uniform(float(minval), float(maxval)),False,8, None
            )
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
            registers[inx + 2].value = regs[2]
            registers[inx + 3].value = regs[3]
        

    @classmethod
    def action_increment(cls, registers, inx, cell, minval=None, maxval=None):
        """Increment value reset with overflow.

        :meta private:
        """
        reg = registers[inx]
        reg2 = registers[inx + 1]
        reg3 = registers[inx + 2]
        reg4 = registers[inx + 3]
        
        if cell.type in (CellType.BITFIELD16,CellType.INT16, CellType.UINT16):
            is_signed=bool( CellType.INT16)
            tmp_reg = [reg.value]
            value = cls.build_value_from_registers(tmp_reg, True,2,is_signed)
            value += 1
            if maxval and value > maxval:
                value = minval
            if minval and value < minval:
                value = minval
            new_regs = cls.build_registers_from_value(value, True,2,is_signed)
            reg.value = new_regs[0]
        elif cell.type in (CellType.BITFIELD32,CellType.INT32, CellType.UINT32):
            is_signed=bool( CellType.INT32)
            tmp_reg = [reg.value, reg2.value]
            value = cls.build_value_from_registers(tmp_reg, True,4,is_signed)
            value += 1
            if maxval and value > maxval:
                value = minval
            if minval and value < minval:
                value = minval
            new_regs = cls.build_registers_from_value(value, True,4,is_signed)
            reg.value = new_regs[0]
            reg2.value = new_regs[1]
        elif cell.type in (CellType.BITFIELD64,CellType.INT64, CellType.UINT64):
            is_signed=bool( CellType.INT64)
            tmp_reg = [reg.value, reg2.value, reg3.value, reg4.value]
            value = cls.build_value_from_registers(tmp_reg, True,8,is_signed)
            value += 1
            if maxval and value > maxval:
                value = minval
            if minval and value < minval:
                value = minval
            new_regs = cls.build_registers_from_value(value, True,8,is_signed)
            reg.value = new_regs[0]
            reg2.value = new_regs[1]
            reg3.value = new_regs[2]
            reg4.value = new_regs[3]
        elif cell.type == CellType.FLOAT32:
            tmp_reg = [reg.value, reg2.value]
            value = cls.build_value_from_registers(tmp_reg, False,4,None)
            value += 1.0
            if maxval and value > maxval:
                value = minval
            if minval and value < minval:
                value = minval
            new_regs = cls.build_registers_from_value(value, False,4,None)
            reg.value = new_regs[0]
            reg2.value = new_regs[1]
        elif cell.type == CellType.FLOAT64:
            tmp_reg = [reg.value, reg2.value, reg3.value, reg4.value]
            value = cls.build_value_from_registers(tmp_reg, False,8,None)
            value += 1.0
            if maxval and value > maxval:
                value = minval
            if minval and value < minval:
                value = minval
            new_regs = cls.build_registers_from_value(value, False,8,None)
            reg.value = new_regs[0]
            reg2.value = new_regs[1]
            reg3.value = new_regs[2]
            reg4.value = new_regs[3]

    @classmethod
    def action_timestamp(cls, registers, inx, _cell, **_kwargs):
        """Set current time.

        :meta private:
        """
        system_time = datetime.now()
        registers[inx].value = system_time.year
        registers[inx + 1].value = system_time.month - 1
        registers[inx + 2].value = system_time.day
        registers[inx + 3].value = system_time.weekday() + 1
        registers[inx + 4].value = system_time.hour
        registers[inx + 5].value = system_time.minute
        registers[inx + 6].value = system_time.second

    @classmethod
    def action_reset(cls, _registers, _inx, _cell, **_kwargs):
        """Reboot server.

        :meta private:
        """
        raise RuntimeError("RESET server")

    @classmethod
    def action_uptime(cls, registers, inx, cell, **_kwargs):
        """Return uptime in seconds.

        :meta private:
        """
        value = int(datetime.now().timestamp()) - cls.start_time + 1

        if cell.type in (CellType.BITFIELD16, CellType.UINT16):
            registers[inx].value = value
        elif cell.type == CellType.FLOAT32:
            regs = cls.build_registers_from_value(value, False,4,None)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type == CellType.UINT32:
            regs = cls.build_registers_from_value(value, True,4,False)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type == CellType.FLOAT64:
            regs = cls.build_registers_from_value(value, False,8,None)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type == CellType.UINT64:
            regs = cls.build_registers_from_value(value, True,8,False)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
    # --------------------------------------------
    # Internal helper methods
    # --------------------------------------------

    def validate_type(self, func_code, real_address, count) -> bool:
        """Check if request is done against correct type.

        :meta private:
        """
        check: tuple
        if func_code in self._bits_func_code:
            # Bit access
            check = (CellType.BITFIELD16, -1)
            reg_step = 1
        elif count % 2:
            # 16 bit access
            check = (CellType.BITFIELD16,CellType.INT16,CellType.UINT16, CellType.STRING)
            reg_step = 1
        elif count % 4:
            check = (CellType.BITFIELD32,CellType.INT32,CellType.UINT32, CellType.FLOAT32, CellType.STRING)
            reg_step = 2
        elif count % 8:
            check = (CellType.BITFIELD64,CellType.INT64,CellType.UINT64, CellType.FLOAT64)
            reg_step = 4
        for i in range(real_address, real_address + count, reg_step):
            if self.registers[i].type in check:
                continue
            if self.registers[i].type is CellType.NEXT:
                continue
            return False
        return True

    @classmethod
    def build_registers_from_value(cls, value, is_int,n_bytes,is_signed):
        """Build registers from int32 or float32."""
        
        if is_int:
            if n_bytes==2 and is_signed is False:
                value_bytes = struct.pack(">H", value)#int.to_bytes(value, 4, "big")
            if n_bytes==2 and is_signed is True:
                value_bytes = struct.pack(">h", value)#int.to_bytes(value, 4, "big")
            if n_bytes==4 and is_signed is False:
                value_bytes = struct.pack(">I", value)#int.to_bytes(value, 4, "big")
            if n_bytes==4 and is_signed is True:
                value_bytes = struct.pack(">i", value)#int.to_bytes(value, 4, "big")
            if n_bytes==8 and is_signed is False:
                value_bytes = struct.pack(">Q", value)#int.to_bytes(value, 4, "big")
            if n_bytes==8 and is_signed is True:
                value_bytes = struct.pack(">q", value)#int.to_bytes(value, 4, "big")
        else:
            if n_bytes==4:
                value_bytes = struct.pack(">f", value)
            if n_bytes==8:
                value_bytes = struct.pack(">d", value)#int.to_bytes(value, 4, "big")  
        
        if n_bytes==2:      
            regs = [0]
            regs[0] = int.from_bytes(value_bytes[:2], "big")
        if n_bytes==4:      
            regs = [0, 0]
            regs[0] = int.from_bytes(value_bytes[:2], "big")
            regs[1] = int.from_bytes(value_bytes[-2:], "big")
        if n_bytes==8:
            regs = [0, 0,0,0]
            regs[0] = int.from_bytes(value_bytes[:2], "big")
            regs[1] = int.from_bytes(value_bytes[2:4], "big")
            regs[2] = int.from_bytes(value_bytes[4:6], "big")
            regs[3] = int.from_bytes(value_bytes[6:8], "big")
            
        return regs

    @classmethod
    def build_value_from_registers(cls, registers, is_int,n_bytes,is_signed):
        """Build int16,int32,int64 or float32 value from registers."""
        if n_bytes==2:
            value_bytes = int.to_bytes(registers[0], 2, "big")  
        if n_bytes==4:
            value_bytes = int.to_bytes(registers[0], 2, "big") + int.to_bytes(registers[1], 2, "big") 
        if n_bytes==8:  
            value_bytes = int.to_bytes(registers[0], 2, "big") + int.to_bytes(registers[1], 2, "big") + int.to_bytes( registers[2], 2, "big" )+ int.to_bytes(registers[3], 2, "big" )
        
        if is_int:
            if n_bytes==2 and is_signed is False:
                value = struct.unpack(">H", value_bytes)
            if n_bytes==2 and is_signed is True:
                value = struct.unpack(">h", value_bytes)
            if n_bytes==4 and is_signed is False:
                value = struct.unpack(">I", value_bytes)
            if n_bytes==4 and is_signed is True:
                value = struct.unpack(">i", value_bytes)
            if n_bytes==8 and is_signed is False:
                value = struct.unpack(">Q", value_bytes)
            if n_bytes==8 and is_signed is True:
                value = struct.unpack(">q", value_bytes)
        else:
            if n_bytes==4:
                value = struct.unpack(">f", value_bytes)
            if n_bytes==8:
                value = struct.unpack(">d", value_bytes)
        return value[0]
    
       
