"""Test datastore."""
import json

import pytest

from pymodbus.datastore import ModbusSimulatorContext
from pymodbus.datastore.simulator import (
    CELL_ACCESS_INVALID,
    CELL_ACCESS_RO,
    CELL_ACCESS_RW,
    CELL_TYPE_BITS,
    CELL_TYPE_STRING,
    CELL_TYPE_STRING_NEXT,
    CELL_TYPE_UINT16,
    CELL_TYPE_UINT32,
    CELL_TYPE_UINT32_NEXT,
    Cell,
)


FX_READ = 1
FX_WRITE = 5


class TestSimulator:
    """Unittest for the pymodbus.Simutor module."""

    simulator = None
    json_dict = None

    def setup_method(self):
        """Do simulator test setup."""
        self.json_dict = {
            "registers": 63,
            "invalid_address": {
                "registers": [
                    [2, 2],
                ]
            },
            "write_allowed": {
                "registers": [
                    [3, 3],
                ]
            },
            "type_uint16": {
                "value": 0,
                "registers": [
                    {"registers": [3, 3], "value": 4660},
                    {"registers": [4, 4], "action": "reset"},
                    {"registers": [5, 11], "value": 0, "action": "timestamp"},
                ],
            },
            "type_uint32": {
                "value": 5,
                "registers": [
                    [12, 13],
                    {"registers": [14, 15], "value": 19088743, "action": "increment"},
                ],
            },
            "type_bits": {
                "value": "0102",
                "action": "",
                "registers": [
                    [16, 16],
                    {"registers": [17, 18], "value": "F1F2F3F4", "action": "random"},
                ],
            },
            "type_string": {
                "value": "  ",
                "registers": [
                    {"registers": [19, 20], "value": "Str"},
                ],
            },
            "repeat_address": {
                "registers": [{"registers": [0, 20], "repeat": [21, 63]}]
            },
        }
        self.simulator = ModbusSimulatorContext()
        self.simulator.load_dict(self.json_dict, None)

    def test_simulator_load(self, tmp_path):
        """Test load from file and from dict."""
        filepath = f"{tmp_path}/test_load.json"
        with open(filepath, "w", encoding="latin-1") as json_file:
            json.dump(self.json_dict, json_file)
        sim_file = ModbusSimulatorContext()
        sim_file.load_file(filepath, None)
        sim_dict = ModbusSimulatorContext()
        sim_dict.load_dict(self.json_dict, None)
        len_sim_file = len(sim_file.registers)
        assert len_sim_file == len(sim_dict.registers)
        for i in range(len_sim_file):
            entry = sim_dict.registers[i]
            if entry.action:
                sim_dict.registers[i].action = entry.action.__name__
            entry = sim_file.registers[i]
            if entry.action:
                sim_file.registers[i].action = entry.action.__name__
        assert sim_file.registers == sim_dict.registers

    def test_simulator_registers(self):
        """Test validate method."""
        test_registers = [
            # register 0
            Cell(None, CELL_ACCESS_INVALID, None, None),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, None),
            Cell(None, CELL_ACCESS_INVALID, None, None),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RW, 4660, None),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, self.simulator.action_reset),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, self.simulator.action_timestamp),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, None),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, None),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, None),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, None),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, None),
            Cell(CELL_TYPE_UINT16, CELL_ACCESS_RO, 0, None),
            # register 12
            Cell(CELL_TYPE_UINT32, CELL_ACCESS_RO, 0, None),
            Cell(CELL_TYPE_UINT32_NEXT, CELL_ACCESS_RO, 5),
            Cell(
                CELL_TYPE_UINT32,
                CELL_ACCESS_RO,
                291,
                self.simulator.action_increment,
            ),  # --> 291
            Cell(CELL_TYPE_UINT32_NEXT, CELL_ACCESS_RO, 17767, None),  # -->   19088743
            # register 16
            Cell(CELL_TYPE_BITS, CELL_ACCESS_RO, 258, None),
            Cell(
                CELL_TYPE_BITS, CELL_ACCESS_RO, 4059231220, self.simulator.action_random
            ),  # --> 61938
            Cell(
                CELL_TYPE_BITS, CELL_ACCESS_RO, 4059231220, self.simulator.action_random
            ),  # --> 62452
            # register 19
            Cell(CELL_TYPE_STRING, CELL_ACCESS_RO, "St", None),
            Cell(CELL_TYPE_STRING_NEXT, CELL_ACCESS_RO, "r", None),
        ]

        for repetition in range(0, 2):
            for i, test_cell in enumerate(test_registers):
                assert (
                    test_cell == self.simulator.registers[i + 21 * repetition]
                ), f"failed in repeat {repetition} register {i}"

    @pytest.mark.parametrize(
        "func_code,address,count,expected",
        [
            (FX_READ, 0, 1, False),
            (FX_READ, 1, 2, False),
            (FX_READ, 2, 1, False),
            (FX_WRITE, 2, 1, False),
            (FX_WRITE, 3, 2, False),
            (FX_READ, 200, 1, False),
            (FX_READ, 1, 1, True),
            (FX_WRITE, 3, 1, True),
            (FX_READ, 5, 10, True),
        ],
    )
    def test_simulator_validate(self, func_code, address, count, expected):
        """Test validate call."""
        assert self.simulator.validate(func_code, address, count) == expected

    def test_simulator_get_values(self):
        """Test simulator get values."""
        assert self.simulator.getValues(FX_READ, 3) == [4660]
        assert self.simulator.getValues(FX_READ, 3, count=2) == [4660, 0]

    def test_simulator_set_values(self):
        """Test simulator set values."""

        self.simulator.setValues(FX_WRITE, 3, values=[5])
        assert self.simulator.getValues(FX_READ, 3) == [5]
