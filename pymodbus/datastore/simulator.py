"""Pymodbus ModbusSimulatorContext."""
import dataclasses
import logging
import random
import struct
import sys
from datetime import datetime
from typing import Callable, Dict


_logger = logging.getLogger()


CELL_TYPE_NONE = " "
CELL_TYPE_BIT = "B"
CELL_TYPE_UINT16 = "i"
CELL_TYPE_UINT32 = "I"
CELL_TYPE_FLOAT32 = "F"
CELL_TYPE_STRING = "S"
CELL_TYPE_NEXT = "n"
CELL_TYPE_INVALID = "X"

WORD_SIZE = 16


@dataclasses.dataclass
class Cell:
    """Handle a single cell."""

    type: int = CELL_TYPE_NONE
    access: bool = False
    value: int = 0
    action: int = 0
    count_read: int = 0
    count_write: int = 0


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
    method: str = "method"
    next: str = "next"
    random: str = "random"
    register: str = "register"
    repeat: str = "repeat"
    reset: str = "reset"
    setup: str = "setup"
    shared_blocks: str = "shared blocks"
    timestamp: str = "timestamp"
    repeat_to: str = "to"
    type: str = "type"
    type_bits = "bits"
    type_exception: str = "type exception"
    type_none: str = "none"
    type_uint16: str = "uint16"
    type_uint32: str = "uint32"
    type_float32: str = "float32"
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

    def __init__(self):
        """Initialize."""
        self.config_types = {
            Label.type_bits: {
                Label.type: CELL_TYPE_BIT,
                Label.next: None,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_bits,
            },
            Label.type_uint16: {
                Label.type: CELL_TYPE_UINT16,
                Label.next: None,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_uint16,
            },
            Label.type_uint32: {
                Label.type: CELL_TYPE_UINT32,
                Label.next: CELL_TYPE_NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_uint32,
            },
            Label.type_float32: {
                Label.type: CELL_TYPE_FLOAT32,
                Label.next: CELL_TYPE_NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_float32,
            },
            Label.type_string: {
                Label.type: CELL_TYPE_STRING,
                Label.next: CELL_TYPE_NEXT,
                Label.value: 0,
                Label.action: None,
                Label.method: self.handle_type_string,
            },
        }
        self.endianness = sys.byteorder

    def handle_type_bits(self, registers, reg_count, start, stop, value, action):
        """Handle type bits.

        :meta private:
        """
        for i in range(start, stop):
            if i >= reg_count:
                raise RuntimeError(
                    f'Error section "{Label.type_bits}" addr {start},  {stop} out of range'
                )
            if registers[i].type != CELL_TYPE_NONE:
                txt = f'ERROR Configuration invalid in section "{Label.type_bits}" register {i} already defined'
                raise RuntimeError(txt)
            registers[i].value = value
            registers[i].type = CELL_TYPE_BIT
            registers[i].action = action

    def handle_type_uint16(self, registers, reg_count, start, stop, value, action):
        """Handle type uint16.

        :meta private:
        """
        for i in range(start, stop):
            if i >= reg_count:
                raise RuntimeError(
                    f'Error section "{Label.type_uint16}" addr {start},  {stop} out of range'
                )
            if registers[i].type != CELL_TYPE_NONE:
                txt = f'ERROR Configuration invalid in section "{Label.type_uint16}" register {i} already defined'
                raise RuntimeError(txt)
            registers[i].value = value
            registers[i].type = CELL_TYPE_UINT16
            registers[i].action = action

    def handle_type_uint32(self, registers, reg_count, start, stop, value, action):
        """Handle type uint32.

        :meta private:
        """
        regs = ModbusSimulatorContext.build_registers_from_value(value, True)
        for i in range(start, stop, 2):
            if i + 1 >= reg_count:
                raise RuntimeError(
                    f'Error section "{Label.type_uint32}" addr {start},  {stop} out of range'
                )
            if registers[i].type != CELL_TYPE_NONE:
                txt = f'ERROR Configuration invalid in section "{Label.type_uint32}" register {i} already defined'
                raise RuntimeError(txt)
            registers[i].value = regs[0]
            registers[i].type = CELL_TYPE_UINT32
            registers[i].action = action
            j = i + 1
            if registers[j].type != CELL_TYPE_NONE:
                txt = f'ERROR Configuration invalid in section "{Label.type_uint32}" register {j} already defined'
                raise RuntimeError(txt)
            registers[j].value = regs[1]
            registers[j].type = CELL_TYPE_NEXT

    def handle_type_float32(self, registers, reg_count, start, stop, value, action):
        """Handle type uint32.

        :meta private:
        """
        regs = ModbusSimulatorContext.build_registers_from_value(value, False)
        for i in range(start, stop, 2):
            if i + 1 >= reg_count:
                raise RuntimeError(
                    f'Error section "{Label.type_float32}" addr {start},  {stop} out of range'
                )
            if registers[i].type != CELL_TYPE_NONE:
                txt = f'ERROR Configuration invalid in section "{Label.type_float32}" register {i} already defined'
                raise RuntimeError(txt)
            registers[i].value = regs[0]
            registers[i].type = CELL_TYPE_FLOAT32
            registers[i].action = action
            j = i + 1
            if registers[j].type != CELL_TYPE_NONE:
                txt = f'ERROR Configuration invalid in section "{Label.type_float32}" register {j} already defined'
                raise RuntimeError(txt)
            registers[j].value = regs[1]
            registers[j].type = CELL_TYPE_NEXT

    def handle_type_string(self, registers, reg_count, start, stop, value, action):
        """Handle type string.

        :meta private:
        """
        regs = stop - start
        reg_len = regs * 2
        if len(value) > reg_len:
            value = value[:reg_len]
        else:
            value = value.ljust(reg_len)
        for i in range(stop - start):
            inx = start + i
            if i + 1 >= reg_count:
                raise RuntimeError(
                    f'Error section "{Label.type_string}" addr {start},  {stop} out of range'
                )
            if registers[inx].type != CELL_TYPE_NONE:
                txt = f'ERROR Configuration invalid in section "{Label.type_string}" register {inx} already defined'
                raise RuntimeError(txt)
            registers[inx].value = int.from_bytes(
                bytes(value[i * 2 : (i + 1) * 2], "UTF-8"), "big"
            )
            registers[inx].type = CELL_TYPE_STRING if not i else CELL_TYPE_NEXT
            registers[start].action = action

    def handle_setup_section(self, config, actions):
        """Load setup section"""
        layout = Label.try_get(Label.setup, config)
        offset = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
            15: 0,
            16: 0,
            22: 0,
            23: 0,
        }
        size_co = Label.try_get(Label.co_size, layout)
        size_di = Label.try_get(Label.di_size, layout)
        size_hr = Label.try_get(Label.hr_size, layout)
        size_ir = Label.try_get(Label.ir_size, layout)
        if Label.try_get(Label.shared_blocks, layout):
            total_size = 0
            for i in (size_co, size_di, size_hr, size_ir):
                if i > total_size:
                    total_size = i
        else:
            offset[1] = 0
            offset[5] = 0
            offset[15] = 0
            total_size = size_co
            offset[2] = total_size
            total_size += size_di
            offset[4] = total_size
            total_size = size_ir
            offset[3] = total_size
            offset[6] = total_size
            offset[16] = total_size
            offset[22] = total_size
            offset[23] = total_size
            total_size += size_hr
        first_cell = Cell()
        registers = [dataclasses.replace(first_cell) for i in range(total_size)]
        defaults = Label.try_get(Label.defaults, layout)
        type_exception = Label.try_get(Label.type_exception, layout)
        defaults_value = Label.try_get(Label.value, defaults)
        defaults_action = Label.try_get(Label.action, defaults)
        for key, entry in self.config_types.items():
            entry[Label.value] = Label.try_get(key, defaults_value)
            if (action := Label.try_get(key, defaults_action)) not in actions:
                txt = f"ERROR Configuration invalid, illegal action {key} in {defaults_action}"
                raise RuntimeError(txt)
            entry[Label.action] = action
        return registers, offset, type_exception

    def handle_invalid_address(self, registers, reg_count, config):
        """Handle invalid address"""
        for entry in Label.try_get(Label.invalid, config):
            if isinstance(entry, int):
                entry = [entry, entry]
            for i in range(entry[0], entry[1] + 1):
                if i >= reg_count:
                    raise RuntimeError(
                        f'Error section "{Label.invalid}" addr {entry} out of range'
                    )
                if registers[i].type != CELL_TYPE_NONE:
                    txt = f'ERROR Configuration invalid in section "invalid" register {i} already defined'
                    raise RuntimeError(txt)
                registers[i].type = CELL_TYPE_INVALID

    def handle_write_allowed(self, registers, reg_count, config):
        """Handle write allowed"""
        for entry in Label.try_get(Label.write, config):
            if isinstance(entry, int):
                entry = [entry, entry]
            for i in range(entry[0], entry[1] + 1):
                if i >= reg_count:
                    raise RuntimeError(
                        f'Error section "{Label.write}" addr {entry} out of range'
                    )
                if registers[i].type in (CELL_TYPE_NONE, CELL_TYPE_INVALID):
                    txt = f'ERROR Configuration invalid in section "write" register {i} not defined'
                    raise RuntimeError(txt)
                registers[i].access = True

    def handle_types(self, registers, actions, reg_count, config):
        """Handle the different types"""
        for section, type_entry in self.config_types.items():
            layout = Label.try_get(section, config)
            for entry in layout:
                if not isinstance(entry, dict):
                    entry = {Label.addr: entry}
                if not isinstance(Label.try_get(Label.addr, entry), list):
                    entry[Label.addr] = [entry[Label.addr], entry[Label.addr]]
                type_entry[Label.method](
                    registers,
                    reg_count,
                    entry[Label.addr][0],
                    entry[Label.addr][1] + 1,
                    entry.get(Label.value, type_entry[Label.value]),
                    actions[entry.get("action", type_entry[Label.action])],
                )

    def handle_repeat(self, registers, reg_count, config):
        """Handle repeat.

        :meta private:
        """
        for entry in Label.try_get(Label.repeat, config):
            addr = Label.try_get(Label.addr, entry)
            copy_start = addr[0]
            copy_end = addr[1]
            copy_inx = copy_start - 1
            addr_to = Label.try_get(Label.repeat_to, entry)
            for inx in range(addr_to[0], addr_to[1] + 1):
                copy_inx = copy_start if copy_inx >= copy_end else copy_inx + 1
                if inx >= reg_count:
                    raise RuntimeError(
                        f'Error section "{Label.repeat}" entry {entry} out of range'
                    )
                registers[inx] = dataclasses.replace(registers[copy_inx])

    def setup(self, config, actions) -> None:
        """Load layout from dict with json structure.

        :meta private:
        """
        registers, offset, typ_exc = self.handle_setup_section(config, actions)
        reg_count = len(registers)
        self.handle_invalid_address(registers, reg_count, config)
        self.handle_types(registers, actions, reg_count, config)
        self.handle_write_allowed(registers, reg_count, config)
        self.handle_repeat(registers, reg_count, config)
        for i in range(reg_count):
            if registers[i].type == CELL_TYPE_NONE:
                registers[i].type = CELL_TYPE_INVALID

        return (registers, offset, typ_exc, reg_count)


class ModbusSimulatorContext:
    """Modbus simulator

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
                        "bits": 0x01,
                        "uint16": 122,
                        "uint32": 67000,
                        "float32": 127.4,
                        "string": " ",
                    },
                    "action": {  --> default action (can be overwritten)
                        "bits": None,
                        "uint16": None,
                        "uint32": None,
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
            "bits": [  --> Define bits (1 register == 1 byte)
                [30, 31],  --> start, end registers, repeated as needed
                {"addr": [32, 34], "value": 0xF1},  --> with value
                {"addr": [35, 36], "action": "increment"},  --> with action
                {"addr": [37, 38], "action": "increment", "value": 0xF1}  --> with action and value
            ],
            "uint16": [  --> Define uint16 (1 register == 2 bytes)
                --> same as type_bits
            ],
            "uint32": [  --> Define 32 bit integers (2 registers == 4 bytes)
                --> same as type_bits
            ],
            "float32": [  --> Define 32 bit floats (2 registers == 4 bytes)
                --> same as type_bits
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
        self, config: Dict[str, any], custom_actions: Dict[str, Callable]
    ) -> None:
        """Initialize."""
        self.action_names = {
            Label.increment: self.action_increment,
            Label.register: self.action_register,
            Label.random: self.action_random,
            Label.reset: self.action_reset,
            Label.timestamp: self.action_timestamp,
            Label.uptime: self.action_uptime,
        }
        if custom_actions:
            self.action_names.update(custom_actions)
        j = len(self.action_names) + 1
        self.action_inx_to_name = ["None"] * j
        self.action_methods = [None] * j
        j = 1
        for key, method in self.action_names.items():
            self.action_inx_to_name[j] = key
            self.action_methods[j] = method
            self.action_names[key] = j
            j += 1
        self.action_names[None] = 0
        self.type_names = {
            Label.type_none: CELL_TYPE_NONE,
            Label.type_bits: CELL_TYPE_BIT,
            Label.type_uint16: CELL_TYPE_UINT16,
            Label.type_uint32: CELL_TYPE_UINT32,
            Label.type_float32: CELL_TYPE_FLOAT32,
            Label.type_string: CELL_TYPE_STRING,
            Label.next: CELL_TYPE_NEXT,
            Label.invalid: CELL_TYPE_INVALID,
            Label.any: None,
        }
        res = Setup().setup(config, self.action_names)
        self.registers = res[0]
        self.offset = res[1]
        self.type_exception = res[2]
        self.register_count = res[3]

    # --------------------------------------------
    # Modbus server interface
    # --------------------------------------------

    _write_func_code = (5, 6, 15, 16, 22, 23)
    _bits_func_code = (1, 2, 5, 15)

    def validate(self, func_code, address, count=1):
        """Check to see if the request is in range.

        :meta private:
        """
        if func_code in self._bits_func_code:
            # Bit count, correct to register count
            count = int((count + WORD_SIZE - 1) / WORD_SIZE)
            address = int(address / 16)
        real_address = self.offset[func_code] + address
        if real_address <= 0 or real_address > self.register_count:
            return False

        fx_write = func_code in self._write_func_code
        for i in range(real_address, real_address + count):
            reg = self.registers[i]
            if reg.type == CELL_TYPE_INVALID:
                return False
            if fx_write and not reg.access:
                return False
        if self.type_exception:
            return self.validate_type(func_code, real_address, count)
        return True

    def getValues(self, func_code, address, count=1):  # pylint: disable=invalid-name
        """Return the requested values of the datastore.

        :meta private:
        """
        result = []
        if func_code not in self._bits_func_code:
            real_address = self.offset[func_code] + address
            for i in range(real_address, real_address + count):
                reg = self.registers[i]
                if reg.action:
                    self.action_methods[reg.action](self.registers, i, reg)
                self.registers[i].count_read += 1
                result.append(reg.value)
        else:
            # bit access
            real_address = self.offset[func_code] + int(address / 16)
            bit_index = address % 16
            reg_count = int((count + bit_index + 15) / 16)
            for i in range(real_address, real_address + reg_count):
                reg = self.registers[i]
                if reg.action:
                    self.action_methods[reg.action](i, reg)
                self.registers[i].count_read += 1
                while count and bit_index < 16:
                    result.append(bool(reg.value & (2**bit_index)))
                    count -= 1
                    bit_index += 1
                bit_index = 0
        return result

    def setValues(self, func_code, address, values):  # pylint: disable=invalid-name
        """Set the requested values of the datastore.

        :meta private:
        """
        if func_code not in self._bits_func_code:
            real_address = self.offset[func_code] + address
            for value in values:
                self.registers[real_address].value = value
                self.registers[real_address].count_write += 1
                real_address += 1
            return

        # bit access
        real_address = self.offset[func_code] + int(address / 16)
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
    def action_register(cls, registers, inx, cell):
        """Update with register number.

        :meta private:
        """
        if cell.type == CELL_TYPE_BIT:
            registers[inx].value = inx
        elif cell.type == CELL_TYPE_FLOAT32:
            regs = cls.build_registers_from_value(float(inx), False)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type == CELL_TYPE_UINT16:
            registers[inx].value = inx
        elif cell.type == CELL_TYPE_UINT32:
            regs = cls.build_registers_from_value(inx, True)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]

    @classmethod
    def action_random(cls, registers, inx, cell):
        """Update with random value.

        :meta private:
        """
        if cell.type == CELL_TYPE_BIT:
            registers[inx].value = random.randint(0, 65536)
        elif cell.type == CELL_TYPE_FLOAT32:
            regs = cls.build_registers_from_value(random.uniform(0.0, 65000.0), False)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type == CELL_TYPE_UINT16:
            registers[inx].value = random.randint(0, 65536)
        elif cell.type == CELL_TYPE_UINT32:
            regs = cls.build_registers_from_value(
                int(random.uniform(0.0, 65000.0)), True
            )
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]

    @classmethod
    def action_increment(cls, registers, inx, cell):
        """Increment value reset with overflow.

        :meta private:
        """
        if cell.type == CELL_TYPE_BIT:
            registers[inx].value += 1
        elif cell.type == CELL_TYPE_FLOAT32:
            value = cls.build_value_from_registers(registers[inx : inx + 2], False)
            value += 1.0
            regs = cls.build_registers_from_value(value, False)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type == CELL_TYPE_UINT16:
            registers[inx].value += 1
        elif cell.type == CELL_TYPE_UINT32:
            value = cls.build_value_from_registers(registers[inx : inx + 2], True)
            value += 1
            regs = cls.build_registers_from_value(value, True)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]

    @classmethod
    def action_timestamp(cls, registers, inx, _cell):
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
    def action_reset(cls, _registers, _inx, _cell):
        """Reboot server.

        :meta private:
        """
        raise RuntimeError("RESET server")

    @classmethod
    def action_uptime(cls, registers, inx, cell):
        """Return uptime in seconds.

        :meta private:
        """
        value = int(datetime.now().timestamp()) - cls.start_time

        if cell.type == CELL_TYPE_BIT:
            registers[inx].value = 0
        elif cell.type == CELL_TYPE_FLOAT32:
            regs = cls.build_registers_from_value(value, False)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]
        elif cell.type == CELL_TYPE_UINT16:
            registers[inx].value = value
        elif cell.type == CELL_TYPE_UINT32:
            regs = cls.build_registers_from_value(value, True)
            registers[inx].value = regs[0]
            registers[inx + 1].value = regs[1]

    # --------------------------------------------
    # Internal helper methods
    # --------------------------------------------

    def validate_type(self, func_code, real_address, count):
        """Check if request is done against correct type

        :meta private:
        """

        if func_code in self._bits_func_code:
            # Bit access
            check = CELL_TYPE_BIT
            reg_step = 1
        elif count % 2:
            # 16 bit access
            check = (CELL_TYPE_UINT16, CELL_TYPE_STRING)
            reg_step = 1
        else:
            check = (CELL_TYPE_UINT32, CELL_TYPE_FLOAT32, CELL_TYPE_STRING)
            reg_step = 2

        for i in range(  # pylint: disable=consider-using-any-or-all
            real_address, real_address + count, reg_step
        ):
            if self.registers[i].type not in check:
                return False
        return True

    @classmethod
    def build_registers_from_value(cls, value, is_int):
        """Build registers from int32 or float32"""
        regs = [0, 0]
        if is_int:
            value_bytes = int.to_bytes(value, 4, "big")
        else:
            value_bytes = struct.pack("f", value)
        regs[0] = int.from_bytes(value_bytes[:2], "big")
        regs[1] = int.from_bytes(value_bytes[-2:], "big")
        return regs

    @classmethod
    def build_value_from_registers(cls, registers, is_int):
        """Build registers from int32 or float32"""
        value_bytes = int.to_bytes(registers[0], 2, "big") + int.to_bytes(
            registers[1], 2, "big"
        )
        if is_int:
            value = int.from_bytes(value_bytes, "big")
        else:
            value = struct.unpack("f", value_bytes)[0]
        return value
