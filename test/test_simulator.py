"""Test datastore."""
import asyncio
import copy
import logging

import pytest

from examples.client_async import setup_async_client
from examples.helper import Commandline
from examples.server_simulator import run_server_simulator, setup_simulator
from pymodbus import pymodbus_apply_logging_config
from pymodbus.datastore import ModbusSimulatorContext
from pymodbus.datastore.simulator import Cell, CellType, Label
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
            [33, 38],
        ],
        "bits": [
            5,
            [7, 8],
            {"addr": 10, "value": 0x81},
            {"addr": [11, 12], "value": 0x04342},
            {"addr": 13, "action": "random"},
            {"addr": 14, "value": 15, "action": "reset"},
        ],
        "uint16": [
            {"addr": 16, "value": 3124},
            {"addr": [17, 18], "value": 5678},
            {
                "addr": [19, 20],
                "value": 14661,
                "action": "increment",
                "args": {"min": 1, "max": 100},
            },
        ],
        "uint32": [
            {"addr": [21, 22], "value": 3124},
            {"addr": [23, 26], "value": 5678},
            {"addr": [27, 30], "value": 345000, "action": "increment"},
            {
                "addr": [31, 32],
                "value": 50,
                "action": "random",
                "kwargs": {"min": 10, "max": 80},
            },
        ],
        "float32": [
            {"addr": [33, 34], "value": 3124.5},
            {"addr": [35, 38], "value": 5678.19},
            {"addr": [39, 42], "value": 345000.18, "action": "increment"},
        ],
        "string": [
            {"addr": [43, 44], "value": "Str"},
            {"addr": [45, 48], "value": "Strxyz12"},
        ],
        "repeat": [{"addr": [0, 48], "to": [49, 147]}],
    }

    test_registers = [
        Cell(),
        Cell(),
        Cell(),
        Cell(),
        Cell(),
        Cell(type=CellType.BITS, access=True, value=0x0708),
        Cell(type=CellType.INVALID),
        Cell(type=CellType.BITS, access=True, value=0x0708),
        Cell(type=CellType.BITS, access=True, value=0x0708),
        Cell(type=CellType.INVALID),
        Cell(type=CellType.BITS, value=0x81),  # 10
        Cell(type=CellType.BITS, value=0x4342),
        Cell(type=CellType.BITS, value=0x4342),
        Cell(type=CellType.BITS, value=1800, action=2),
        Cell(type=CellType.BITS, value=15, action=3),
        Cell(type=CellType.INVALID),
        Cell(type=CellType.UINT16, access=True, value=3124),
        Cell(type=CellType.UINT16, access=True, value=5678),
        Cell(type=CellType.UINT16, access=True, value=5678),
        Cell(type=CellType.UINT16, value=14661, action=1),
        Cell(type=CellType.UINT16, value=14661, action=1),  # 20
        Cell(type=CellType.UINT32, access=True),
        Cell(type=CellType.NEXT, access=True, value=3124),
        Cell(type=CellType.UINT32, access=True),
        Cell(type=CellType.NEXT, access=True, value=5678),
        Cell(type=CellType.UINT32, access=True),
        Cell(type=CellType.NEXT, access=True, value=5678),
        Cell(type=CellType.UINT32, value=5, action=1),
        Cell(type=CellType.NEXT, value=17320),
        Cell(type=CellType.UINT32, value=5, action=1),
        Cell(type=CellType.NEXT, value=17320),  # 30
        Cell(type=CellType.UINT32, action=2, action_kwargs={"min": 10, "max": 80}),
        Cell(type=CellType.NEXT, value=50),
        Cell(type=CellType.FLOAT32, access=True, value=72),
        Cell(type=CellType.NEXT, access=True, value=17221),
        Cell(type=CellType.FLOAT32, access=True, value=34161),
        Cell(type=CellType.NEXT, access=True, value=45381),
        Cell(type=CellType.FLOAT32, access=True, value=34161),
        Cell(type=CellType.NEXT, access=True, value=45381),
        Cell(type=CellType.FLOAT32, value=1653, action=1),
        Cell(type=CellType.NEXT, value=43080),  # 40
        Cell(type=CellType.FLOAT32, value=1653, action=1),
        Cell(type=CellType.NEXT, value=43080),
        Cell(type=CellType.STRING, value=int.from_bytes(bytes("St", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("r ", "utf-8"), "big")),
        Cell(type=CellType.STRING, value=int.from_bytes(bytes("St", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("rx", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("yz", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("12", "utf-8"), "big")),
        # 48 MAX before repeat
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
        test_setup = copy.deepcopy(self.default_config)
        self.simulator = ModbusSimulatorContext(test_setup, self.custom_actions)

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
        for offset in (0, 49, 98):
            for i, test_cell in enumerate(self.test_registers):
                reg = self.simulator.registers[i + offset]
                assert reg.type == test_cell.type, f"at index {i} - {offset}"
                assert reg.access == test_cell.access, f"at index {i} - {offset}"
                assert reg.value == test_cell.value, f"at index {i} - {offset}"
                assert reg.action == test_cell.action, f"at index {i} - {offset}"
                assert (
                    reg.action_kwargs == test_cell.action_kwargs
                ), f"at index {i} - {offset}"
                assert (
                    reg.count_read == test_cell.count_read
                ), f"at index {i} - {offset}"
                assert (
                    reg.count_write == test_cell.count_write
                ), f"at index {i} - {offset}"

    def test_simulator_config_verify2(self):
        """Test basic configuration."""
        # Manually build expected memory image and then compare.
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup[Label.setup][Label.shared_blocks] = False
        exc_setup[Label.setup][Label.co_size] = 15
        exc_setup[Label.setup][Label.di_size] = 15
        exc_setup[Label.setup][Label.hr_size] = 15
        exc_setup[Label.setup][Label.ir_size] = 15
        del exc_setup[Label.repeat]
        exc_setup[Label.repeat] = []
        simulator = ModbusSimulatorContext(exc_setup, None)
        assert simulator.register_count == 60
        for i, test_cell in enumerate(self.test_registers):
            reg = simulator.registers[i]
            assert reg.type == test_cell.type, f"at index {i}"
            assert reg.value == test_cell.value, f"at index {i}"

    def test_simulator_invalid_config(self):
        """Test exception for invalid configuration."""
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup["bad section"] = True
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)
        for entry in (
            (Label.type_bits, 5),
            (Label.type_uint16, 16),
            (Label.type_uint32, [31, 32]),
            (Label.type_float32, [33, 34]),
            (Label.type_string, [43, 44]),
        ):
            exc_setup = copy.deepcopy(self.default_config)
            exc_setup[entry[0]].append(entry[1])
            with pytest.raises(RuntimeError):
                ModbusSimulatorContext(exc_setup, None)
        exc_setup = copy.deepcopy(self.default_config)
        del exc_setup[Label.type_bits]
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup[Label.type_string][1][Label.value] = "very long string again"
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup[Label.setup][Label.defaults][Label.action][
            Label.type_bits
        ] = "bad action"
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup[Label.invalid].append(700)
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup[Label.write].append(700)
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup[Label.write].append(1)
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup[Label.type_bits].append(700)
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)
        exc_setup = copy.deepcopy(self.default_config)
        exc_setup[Label.repeat][0][Label.repeat_to] = [48, 500]
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(exc_setup, None)

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
        addr = 27
        exp1 = self.simulator.validate(FX_WRITE_REG, addr, 1)
        assert not exp1, f"wrong legal at index {addr}"

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
            (FX_READ_BIT, 256, 1, True),
            (FX_READ_REG, 16, 1, True),
            (FX_READ_REG, 43, 1, True),
            (FX_READ_REG, 21, 1, False),
            (FX_READ_REG, 21, 2, True),
            (FX_READ_REG, 43, 2, True),
            (FX_READ_REG, 45, 4, True),
        ):
            validated = exc_simulator.validate(entry[0], entry[1], entry[2])
            assert entry[3] == validated, f"at entry {entry}"

    def test_simulator_get_values(self):
        """Test simulator get values."""
        for entry in (
            (FX_READ_BIT, 194, 1, [False]),
            (FX_READ_BIT, 83, 1, [True]),
            (FX_READ_BIT, 87, 5, [False] + [True] * 3 + [False]),
            (FX_READ_BIT, 198, 4, [True, False, True, True]),
            (FX_READ_REG, 19, 1, [14662]),
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
        exc_simulator.setValues(FX_WRITE_BIT, 80, [True] * 17)

    def test_simulator_get_text(self):
        """Test get_text_register()."""
        for test_reg, test_entry, test_cell in (
            (1, "1", Cell(type=Label.invalid, action="none", value="0")),
            (5, "5", Cell(type=Label.type_bits, action="none", value="0x708")),
            (
                31,
                "31-32",
                Cell(
                    type=Label.type_uint32,
                    action="random({'min': 10, 'max': 80})",
                    value="50",
                ),
            ),
            (33, "33-34", Cell(type=Label.type_float32, action="none", value="3124.5")),
            (43, "43-44", Cell(type=Label.type_string, action="none", value="Str ")),
        ):
            reg = self.simulator.registers[test_reg]
            entry, cell = self.simulator.get_text_register(test_reg)
            assert entry == test_entry, f"at register {test_reg}"
            assert cell.type == test_cell.type, f"at register {test_reg}"
            assert cell.access == str(reg.access), f"at register {test_reg}"
            assert cell.value == test_cell.value, f"at register {test_reg}"
            assert cell.action == test_cell.action, f"at register {test_reg}"
            assert cell.count_read == str(reg.count_read), f"at register {test_reg}"
            assert cell.count_write == str(reg.count_write), f"at register {test_reg}"

    @pytest.mark.parametrize(
        "func,addr",
        [
            (FX_READ_BIT, 12),
            (FX_READ_REG, 16),
            (FX_READ_REG, 21),
            (FX_READ_REG, 33),
        ],
    )
    @pytest.mark.parametrize(
        "action",
        [
            Label.increment,
            Label.random,
            Label.uptime,
        ],
    )
    def test_simulator_actions(self, func, addr, action):
        """Test actions."""
        exc_setup = copy.deepcopy(self.default_config)
        exc_simulator = ModbusSimulatorContext(exc_setup, None)
        reg1 = exc_simulator.registers[addr]
        reg2 = exc_simulator.registers[addr + 1]
        reg1.action = exc_simulator.action_name_to_id[action]
        reg1.value = 0
        reg2.value = 0
        if func == FX_READ_BIT:
            addr = addr * 16 - 16 + 14
        values = exc_simulator.getValues(func, addr, 2)
        assert values[0] or values[1]

    def test_simulator_action_timestamp(self):
        """Test action random"""
        exc_setup = copy.deepcopy(self.default_config)
        exc_simulator = ModbusSimulatorContext(exc_setup, None)
        addr = 12
        exc_simulator.registers[addr].action = exc_simulator.action_name_to_id[
            Label.timestamp
        ]
        exc_simulator.getValues(FX_READ_REG, addr, 1)

    def test_simulator_action_reset(self):
        """Test action random"""
        exc_setup = copy.deepcopy(self.default_config)
        exc_simulator = ModbusSimulatorContext(exc_setup, None)
        addr = 12
        exc_simulator.registers[addr].action = exc_simulator.action_name_to_id[
            Label.reset
        ]
        with pytest.raises(RuntimeError):
            exc_simulator.getValues(FX_READ_REG, addr, 1)

    async def test_simulator_example(self):
        """Test datastore simulator example."""
        pymodbus_apply_logging_config(logging.DEBUG)
        # JAN activate.
        args = Commandline.copy()
        args.comm = "tcp"
        args.framer = ModbusSocketFramer
        args.port = 5051
        run_args = setup_simulator(
            args, setup=self.default_config, actions=self.custom_actions
        )
        if args:
            return  # Turn off for now.
        asyncio.create_task(run_server_simulator(run_args))
        await asyncio.sleep(0.1)
        client = setup_async_client(args)
        await client.connect()
        assert client.protocol

        rr = await client.read_holding_registers(16, 1, slave=1)
        assert rr.registers
        await client.close()
        await ServerAsyncStop()
