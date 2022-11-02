"""Pymodbus ModbusSimulatorContext."""
import dataclasses
import json
import logging
import sys
from typing import Callable

from pymodbus.interfaces import IModbusSlaveContext


_logger = logging.getLogger()


CELL_ACCESS_RO = "R"
CELL_ACCESS_RW = "W"
CELL_ACCESS_INVALID = "I"

CELL_TYPE_UINT16 = "H"
CELL_TYPE_UINT32 = "I"
CELL_TYPE_UINT32_NEXT = "i"
CELL_TYPE_STRING = "C"
CELL_TYPE_STRING_NEXT = "c"
CELL_TYPE_BITS = "B"


@dataclasses.dataclass
class Cell:
    """Handle a single cell."""

    type: int = CELL_TYPE_UINT16
    access: str = CELL_ACCESS_RO
    value: int = 0
    action: Callable = None


class ModbusSimulatorContext(IModbusSlaveContext):
    """ModbuSimulatorContext

        loads a memory configuration from a json file
        (see examples/simulator.py for details) and prepares a
        simulation of a device.

        The integration is simple::

            store = ModbusSimulatorContext()

            store.load_file(<json file path>, <action dict>)
            # or
            store.load_dict(<json dict>, <action dict>)

            StartAsyncTcpServer(context=store)

        Now the server will simulate the defined device with features like:

        - invalid addresses
        - write protected addresses
        - optional control of access for string, uint32, bit/bits
        - optional automatic value increment by each read
        - builtin functions for e.g. reset/datetime
        - custom functions invoked by read/write to a specific address

    Description of the json file or dict to be supplied::

        {
        "registers": 200,
        --> Total number of registers
        "invalid_address": {
        --> List of invalid addresses, Read/Write causes invalid address response.
            "registers": [
                [78, 99],
            --> start, end register, repeated as needed
        ]},
        "write_allowed": {
        --> default is ReadOnly, allow write (other addresses causes invalid address response)
            "registers": [
                [5, 5]
                --> start, end register, repeated as needed
                [61, 76],
        ]},
        "type_uint32": {
        --> Define 32 bit integers 2 registers
            "value": 0,
            --> Default value of uint32
            "action": "random",
            --> Default action to use, need to be used with care !
            "registers": [
                [1, 2],
                --> start, end register, repeated as needed
                [3, 6],
                --> start, end register can be a group of int32
                {"registers": [7, 8], "value": 300},
                --> Override default value
                {"registers": [14, 20], "action": "increment"},
                --> Override default action
                {"registers": [14, 20], "value": 117, "action": "increment"},
                --> Override default value and action
        ]},
        "type_string": {
        --> Define strings, variable number of registers (2 bytes)
            "value": "  ",
            --> Default value of string ONLY 1 register, expanded automatically
            "action": "",
            --> Default action to use, need to be used with care !
            "registers": [
                [21, 22],
            --> start, end register, define 1 string
                {"registers": 23, 25], "value": "String"},
                --> start, end register, define 1 string, with value
                {"registers": 26, 27], "action": ""},
                --> start, end register, define 1 string, with action
                {"registers": 28, 29], "action": "", "value": "String"}
                --> start, end register, define 1 string, with action and value
        ]},
        "type_bits": {
        --> Define 16 bit registers
            "value": "0x00",
            --> Default value of register in hex
            "action": "increment",
            --> Default action to use, need to be used with care !
            "registers": [
                [30, 31],
                --> start, end register, repeated as needed
                {"registers": [32, 34], "value": "0xF1F2F3"},
                --> start, end register, with value
                {"registers": [35, 36], "action": "increment"},
                --> start, end register, with action
                {"registers": [37, 38], "action": "increment", "value": "0xF1F2F3"}
                --> start, end register, with action and value
        ]},
        "type_uint16": {
        --> Define uint16 (1 register), This is automatically defined
            "value": 0,
            --> Default value of register
            "action": "random",
            --> Default action to use, need to be used with care !
            "registers": [
                {"registers": [40, 46], "action": "timestamp"},
                --> start, end register, with action
                {"registers": [47, 90], "value": 17},
                --> start, end register, with value
                {"registers": [91, 91], "value": 15, "action": "increment"}
                --> start, end register, with action and value
        ]},
        "repeat_address": {
        --> allows to repeat section e.g. for n devices
            "registers": [
                {"registers": [100, 200], "repeat": [50, 275]}
                --> Repeat registers 100-200 to 50+ until register 275
        ]}}
    """

    # --------------------------------------------
    # External interfaces
    # --------------------------------------------

    def __init__(self) -> None:
        """Initialize."""
        super().__init__()
        self.last_register = 0
        self.registers = []
        self.endian_convert = sys.byteorder == "little"

    def load_file(self, json_path: str, actions_dict: dict) -> None:
        """Load layout from json file.

        :param json_path: A qualified path to the json file.
        :param actions_dict: A dict with "<name>": <function> structure.
        :raises FileNotFound: if the file cannot be opened.
        :raises RuntimeError: if json contains errors (msg explains what)
        """
        with open(json_path, encoding="latin-1") as json_file:
            rules = json.load(json_file)
        self.load_dict(rules, actions_dict)

    def load_dict(self, json_dict: str, actions_dict: dict) -> None:
        """Load layout from dict with json structure.

        :param json_dict: A dict with same structure as json file.
        :param actions_dict: A dict with "<name>": <function> structure.
        :raises RuntimeError: if dict contains errors (msg explains what)
        """

        sections = (
            ("invalid_address", self.handle_invalid_address),
            ("write_allowed", self.handle_write_allowed),
            ("type_uint32", self.handle_type_uint32),
            ("type_string", self.handle_type_string),
            ("type_bits", self.handle_type_bits),
            ("type_uint16", self.handle_type_uint16),
            ("repeat_address", self.handle_repeat_address),
        )
        actions = {
            "random": self.action_random,
            "increment": self.action_increment,
            "timestamp": self.action_timestamp,
            "reset": self.action_reset,
            "": None,
            None: None,
        }
        if actions_dict:
            actions.update(actions_dict)

        entry_registers = "registers"
        entry_value = "value"
        entry_action = "action"

        self.last_register = json_dict[entry_registers]
        self.registers = [Cell() for i in range(self.last_register + 1)]
        self.handle_invalid_address([0, 0], None, None, None)
        for section, method in sections:
            layout = json_dict[section]
            default_value = layout.get(entry_value, None)
            default_action = layout.get(entry_action, None)
            for entry in layout[entry_registers]:
                if not isinstance(entry, dict):
                    entry = {entry_registers: entry}
                if (action := entry.get(entry_action, default_action)) not in actions:
                    raise RuntimeError(f"Action {action} not defined.")
                action_call = actions[action] if action else None
                method(
                    entry[entry_registers],
                    entry.get(entry_value, default_value),
                    action_call,
                    entry,
                )

    # --------------------------------------------
    # Modbus server interface
    # --------------------------------------------

    _write_fx = (5, 6, 15, 22, 23)

    def validate(self, fx, address, count=1):
        """Check to see if the request is in range.

        :meta private:
        """
        if address <= 0 or address + count - 1 > self.last_register:
            return False

        fx_write = fx in self._write_fx
        for i in range(address, address + count):
            reg = self.registers[i]
            if reg.access == CELL_ACCESS_INVALID:
                return False
            if fx_write and not reg.access == CELL_ACCESS_RW:
                return False
        return True

    def getValues(self, fx, address, count=1):
        """Return the requested values of the datastore.

        :meta private:
        """
        result = []
        for i in range(address, address + count):
            if action := self.registers[i].action:
                action(self.registers, i)
            result.append(self.registers[i].value)
        return result

    def setValues(self, fx, address, values):
        """Set the requested values of the datastore.

        :meta private:
        """
        for i, value in enumerate(values):
            if action := self.registers[address + i].action:
                action(self.registers, address + i, values=values[i:])
            self.registers[address + i].value = value

    # --------------------------------------------
    # Internal helper methods
    # --------------------------------------------

    def action_random(self, _registers, address, values=None):
        """Update with random value."""
        print(f"JAN -> {address}, {values}")

    def action_increment(self, _registers, _address, _values=None):
        """Increment value reset with overflow."""

    def action_timestamp(self, _registers, _address, _values=None):
        """Set current time."""

    def action_reset(self, _registers, _address, _values=None):
        """Reboot server."""

    def handle_invalid_address(self, registers, _value, _action, _entry):
        """Handle invalid address."""
        for i in range(registers[0], registers[1] + 1):
            self.registers[i].access = CELL_ACCESS_INVALID
            self.registers[i].value = None
            self.registers[i].action = None
            self.registers[i].type = None

    def handle_write_allowed(self, registers, _value, _action, _entry):
        """Handle write allowed."""
        for i in range(registers[0], registers[1] + 1):
            self.registers[i].access = CELL_ACCESS_RW

    def handle_type_uint32(self, registers, value, action, _entry):
        """Handle type uint32."""
        value_bytes = value.to_bytes(4, "big")
        value_reg1 = int.from_bytes(value_bytes[:2], "big")
        value_reg2 = int.from_bytes(value_bytes[2:4], "big")
        for i in range(registers[0], registers[1] + 1, 2):
            self.registers[i].type = CELL_TYPE_UINT32
            self.registers[i].action = action
            self.registers[i].value = value_reg1
            self.registers[i + 1].type = CELL_TYPE_UINT32_NEXT
            self.registers[i + 1].value = value_reg2

    def handle_type_string(self, registers, value, action, _entry):
        """Handle type string."""
        j = 0
        for i in range(registers[0], registers[1] + 1):
            self.registers[i].type = CELL_TYPE_STRING_NEXT
            self.registers[i].value = value[j : j + 2]
            j += 2
        self.registers[registers[0]].type = CELL_TYPE_STRING
        self.registers[registers[0]].action = action

    def handle_type_bits(self, registers, _value, action, _entry):
        """Handle type bits."""
        value_int = int(_value, 16)
        for i in range(registers[0], registers[1] + 1):
            self.registers[i].type = CELL_TYPE_BITS
            self.registers[i].value = value_int
            self.registers[i].action = action

    def handle_type_uint16(self, registers, value, action, _entry):
        """Handle type uint16."""
        self.registers[registers[0]].action = action
        for i in range(registers[0], registers[1] + 1):
            self.registers[i].type = CELL_TYPE_UINT16
            self.registers[i].value = value

    def handle_repeat_address(self, registers, _value, _action, entry):
        """Handle repeat address."""
        copy_start = registers[0]
        copy_end = registers[1]
        i = copy_start - 1
        for repeat in range(entry["repeat"][0], entry["repeat"][1] + 1):
            i = copy_start if i > copy_end else i + 1
            self.registers[repeat] = dataclasses.replace(self.registers[i])
