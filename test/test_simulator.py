"""Test datastore."""
import asyncio
import copy

from examples.client_async import setup_async_client
from examples.helper import Commandline
from examples.server_simulator import run_server_simulator, setup_simulator
from pymodbus import pymodbus_apply_logging_config
from pymodbus.datastore import ModbusSimulatorContext
from pymodbus.datastore.simulator import (
    CELL_TYPE_BIT,
    CELL_TYPE_FLOAT32,
    CELL_TYPE_INVALID,
    CELL_TYPE_NEXT,
    CELL_TYPE_STRING,
    CELL_TYPE_UINT16,
    CELL_TYPE_UINT32,
    Cell,
)
from pymodbus.server import ServerAsyncStop
from pymodbus.transaction import ModbusSocketFramer


FX_READ_BIT = 1
FX_READ_REG = 3
FX_WRITE_BIT = 5
FX_WRITE_REG = 6


class TestSimulator:
    """Unittest for the pymodbus.Simutor module."""

    simulator = None
    default_config = {
        "setup": {
            "co size": 100,
            "di size": 150,
            "hr size": 200,
            "ir size": 250,
            "shared blocks": True,
            "type exception": False,
            "defaults": {
                "value": {
                    "bits": 0x0708,
                    "uint16": 1,
                    "uint32": 45000,
                    "float32": 127.4,
                    "string": "X",
                },
                "action": {
                    "bits": None,
                    "uint16": None,
                    "uint32": None,
                    "float32": None,
                    "string": None,
                },
            },
        },
        "invalid": [
            1,
            [3, 4],
        ],
        "write": [
            5,
            [7, 8],
            [16, 18],
            [21, 26],
            [31, 36],
        ],
        "bits": [
            5,
            [7, 8],
            {"addr": 10, "value": 0x81},
            {"addr": [11, 12], "value": 0x04342},
            {"addr": 13, "action": "reset"},
            {"addr": 14, "value": 15, "action": "reset"},
        ],
        "uint16": [
            {"addr": 16, "value": 3124},
            {"addr": [17, 18], "value": 5678},
            {"addr": [19, 20], "value": 14661, "action": "increment"},
        ],
        "uint32": [
            {"addr": 21, "value": 3124},
            {"addr": [23, 25], "value": 5678},
            {"addr": [27, 29], "value": 345000, "action": "increment"},
        ],
        "float32": [
            {"addr": 31, "value": 3124.17},
            {"addr": [33, 35], "value": 5678.19},
            {"addr": [37, 39], "value": 345000.18, "action": "increment"},
        ],
        "string": [
            {"addr": [41, 42], "value": "Str"},
            {"addr": [43, 44], "value": "Strxyz"},
        ],
        "repeat": [{"addr": [0, 45], "to": [46, 138]}],
    }

    test_registers = [
        Cell(CELL_TYPE_INVALID, False, 0, 0),
        Cell(CELL_TYPE_INVALID, False, 0, 0),
        Cell(CELL_TYPE_INVALID, False, 0, 0),
        Cell(CELL_TYPE_INVALID, False, 0, 0),
        Cell(CELL_TYPE_INVALID, False, 0, 0),
        Cell(CELL_TYPE_BIT, True, 1800, 0),
        Cell(CELL_TYPE_INVALID, False, 0, 0),
        Cell(CELL_TYPE_BIT, True, 1800, 0),
        Cell(CELL_TYPE_BIT, True, 1800, 0),
        Cell(CELL_TYPE_INVALID, False, 0, 0),
        Cell(CELL_TYPE_BIT, False, 0x81, 0),  # 10
        Cell(CELL_TYPE_BIT, False, 0x4342, 0),
        Cell(CELL_TYPE_BIT, False, 0x4342, 0),
        Cell(CELL_TYPE_BIT, False, 1800, 4),
        Cell(CELL_TYPE_BIT, False, 15, 4),
        Cell(CELL_TYPE_INVALID, False, 0, 0),
        Cell(CELL_TYPE_UINT16, True, 3124, 0),
        Cell(CELL_TYPE_UINT16, True, 5678, 0),
        Cell(CELL_TYPE_UINT16, True, 5678, 0),
        Cell(CELL_TYPE_UINT16, False, 14661, 1),
        Cell(CELL_TYPE_UINT16, False, 14661, 1),  # 20
        Cell(CELL_TYPE_UINT32, True, 0, 0),
        Cell(CELL_TYPE_NEXT, True, 3124, 0),
        Cell(CELL_TYPE_UINT32, True, 0, 0),
        Cell(CELL_TYPE_NEXT, True, 5678, 0),
        Cell(CELL_TYPE_UINT32, True, 0, 0),
        Cell(CELL_TYPE_NEXT, True, 5678, 0),
        Cell(CELL_TYPE_UINT32, False, 5, 1),
        Cell(CELL_TYPE_NEXT, False, 17320, 0),
        Cell(CELL_TYPE_UINT32, False, 5, 1),
        Cell(CELL_TYPE_NEXT, False, 17320, 0),  # 30
        Cell(CELL_TYPE_FLOAT32, True, 47170, 0),
        Cell(CELL_TYPE_NEXT, True, 17221, 0),
        Cell(CELL_TYPE_FLOAT32, True, 34161, 0),
        Cell(CELL_TYPE_NEXT, True, 45381, 0),
        Cell(CELL_TYPE_FLOAT32, True, 34161, 0),
        Cell(CELL_TYPE_NEXT, True, 45381, 0),
        Cell(CELL_TYPE_FLOAT32, False, 1653, 1),
        Cell(CELL_TYPE_NEXT, False, 43080, 0),
        Cell(CELL_TYPE_FLOAT32, False, 1653, 1),
        Cell(CELL_TYPE_NEXT, False, 43080, 0),  # 40
        Cell(CELL_TYPE_STRING, False, int.from_bytes(bytes("St", "utf-8"), "big"), 0),
        Cell(CELL_TYPE_NEXT, False, int.from_bytes(bytes("r ", "utf-8"), "big"), 0),
        Cell(CELL_TYPE_STRING, False, int.from_bytes(bytes("St", "utf-8"), "big"), 0),
        Cell(
            CELL_TYPE_NEXT, False, int.from_bytes(bytes("rx", "utf-8"), "big"), 0
        ),  # 29 MAX before repeat
    ]

    @classmethod
    def custom_action1(cls, _inx, _cell):
        """Test action."""

    @classmethod
    def custom_action2(cls, _inx, _cell):
        """Test action."""

    custom_actions = {
        "custom1": custom_action1,
        "custom2": custom_action2,
    }

    def setup_method(self):
        """Do simulator test setup."""
        self.simulator = ModbusSimulatorContext(
            self.default_config, self.custom_actions
        )

    def test_pack_unpack_values(self):
        """Test the pack unpack methods."""
        value = 32145678
        regs = ModbusSimulatorContext.build_registers_from_value(value, True)
        test_value = ModbusSimulatorContext.build_value_from_registers(regs, True)
        assert value == test_value

        value = 3.14159265358979
        regs = ModbusSimulatorContext.build_registers_from_value(value, False)
        test_value = ModbusSimulatorContext.build_value_from_registers(regs, False)
        assert round(value, 6) == round(test_value, 6)

    def test_simulator_config_verify(self):
        """Test basic configuration."""
        # Manually build expected memory image and then compare.
        assert self.simulator.register_count == 250
        for offset in (0, 46, 92):
            for i, test_cell in enumerate(self.test_registers):
                assert (
                    self.simulator.registers[i + offset].type == test_cell.type
                ), f"at index {i} - {offset}"
                assert (
                    self.simulator.registers[i + offset].access == test_cell.access
                ), f"at index {i} - {offset}"
                assert (
                    self.simulator.registers[i + offset].value == test_cell.value
                ), f"at index {i} - {offset}"
                assert (
                    self.simulator.registers[i + offset].action == test_cell.action
                ), f"at index {i} - {offset}"
        assert self.simulator.registers[138] == self.test_registers[0]

    def test_simulator_validate_illegal(self):
        """Test validation without exceptions"""
        illegal_cell_list = (0, 1, 2, 3, 4, 6, 9, 15)
        write_cell_list = (
            5,
            7,
            8,
            16,
            17,
            18,
            21,
            22,
            23,
            24,
            25,
            26,
            31,
            32,
            33,
            34,
            35,
            36,
        )
        # for func_code in (FX_READ_BIT, FX_READ_REG, FX_WRITE_BIT, FX_WRITE_REG):
        for func_code in (FX_READ_BIT,):
            for addr in range(len(self.test_registers) - 1):
                exp1 = self.simulator.validate(func_code, addr * 16, 1)
                exp2 = self.simulator.validate(func_code, addr * 16, 20)
                # Illegal cell and no write
                if addr in illegal_cell_list:
                    assert not exp1, f"wrong illegal at index {addr}"
                    continue
                if addr + 1 in illegal_cell_list:
                    assert not exp2, f"wrong legal at second index {addr+1}"
                    continue
                if func_code in (FX_WRITE_BIT, FX_WRITE_REG):
                    if addr in write_cell_list:
                        assert not exp1, f"missing write at index {addr}"
                        continue
                    if addr + 1 in illegal_cell_list:
                        assert not exp2, f"missing write at second index {addr+1}"
                        continue
                assert exp1, f"wrong legal at index {addr}"
                assert exp2, f"wrong legal at second index {addr+1}"

    def test_simulator_validate_type(self):
        """Test validate call."""
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup["setup"]["type exception"] = True
        exc_simulator = ModbusSimulatorContext(exc_setup, None)

        for entry in (
            (FX_READ_BIT, 80, 1, True),
            (FX_READ_BIT, 116, 16, True),
            (FX_READ_BIT, 112, 32, True),
            (FX_READ_BIT, 128, 17, False),
            (FX_READ_BIT, 256, 1, False),
            (FX_READ_REG, 16, 1, True),
            (FX_READ_REG, 41, 1, True),
            (FX_READ_REG, 21, 1, False),
            (FX_READ_REG, 21, 2, True),
            (FX_READ_REG, 41, 2, True),
        ):
            validated = exc_simulator.validate(entry[0], entry[1], entry[2])
            assert entry[3] == validated, f"at entry {entry}"

    def test_simulator_get_values(self):
        """Test simulator get values."""
        for entry in (
            (FX_READ_BIT, 80, 1, [False]),
            (FX_READ_BIT, 83, 1, [True]),
            (FX_READ_BIT, 87, 5, [False] + [True] * 3 + [False]),
            (FX_READ_BIT, 190, 4, [True, False, False, True]),
            (FX_READ_REG, 16, 1, [3124]),
            (FX_READ_REG, 16, 2, [3124, 5678]),
        ):
            values = self.simulator.getValues(entry[0], entry[1], entry[2])
            assert entry[3] == values, f"at entry {entry}"

    def test_simulator_set_values(self):
        """Test simulator set values."""
        exc_setup = copy.deepcopy(self.default_config)
        exc_simulator = ModbusSimulatorContext(exc_setup, None)

        value = [31234]
        exc_simulator.setValues(FX_WRITE_REG, 16, value)
        result = exc_simulator.getValues(FX_READ_REG, 16, 1)
        assert value == result
        value = [31234, 189]
        exc_simulator.setValues(FX_WRITE_REG, 16, value)
        result = exc_simulator.getValues(FX_READ_REG, 16, 2)
        assert value == result

        exc_simulator.registers[5].value = 0
        exc_simulator.setValues(FX_WRITE_BIT, 80, [True])
        exc_simulator.setValues(FX_WRITE_BIT, 82, [True])
        exc_simulator.setValues(FX_WRITE_BIT, 84, [True])
        exc_simulator.setValues(FX_WRITE_BIT, 86, [True, False, True])
        result = exc_simulator.getValues(FX_READ_BIT, 80, 8)
        assert [True, False] * 4 == result
        exc_simulator.setValues(FX_WRITE_BIT, 88, [False])
        result = exc_simulator.getValues(FX_READ_BIT, 86, 3)
        assert [True, False, False] == result

    def test_simulator_action_timestamp(self):
        """Test action random"""

    def test_simulator_action_reset(self):
        """Test action random"""

    async def test_simulator_example(self):
        """Test datastore simulator example."""
        pymodbus_apply_logging_config()

        args = Commandline.copy()
        args.comm = "tcp"
        args.framer = ModbusSocketFramer
        args.port = 5021
        run_args = setup_simulator(
            args, setup=self.default_config, actions=self.custom_actions
        )
        asyncio.create_task(run_server_simulator(run_args))
        await asyncio.sleep(0.1)
        client = setup_async_client(args)
        await client.connect()
        assert client.protocol

        rr = await client.read_holding_registers(16, 1, slave=1)
        assert rr.registers
        await client.close()
        await ServerAsyncStop()
