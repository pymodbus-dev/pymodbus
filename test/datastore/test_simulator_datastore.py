#  zuban: ignore
"""Test datastore."""

import copy

import pytest

from pymodbus.constants import ExcCodes
from pymodbus.datastore import CellType, ModbusSimulatorContext
from pymodbus.datastore.simulator import Cell, Label


FX_READ_BIT = 1
FX_READ_REG = 3
FX_WRITE_BIT = 5
FX_WRITE_REG = 6


class TestDatastoreSimulator:
    """Unittest for the pymodbus.Simutor module."""

    default_device = {
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
                    "float64": -42.42,
                    "string": "X",
                },
                "action": {
                    "bits": None,
                    "uint16": None,
                    "uint32": None,
                    "float32": None,
                    "float64": None,
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
            [43, 46],
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
                "args": {"minval": 1, "maxval": 100},
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
                "parameters": {"minval": 10, "maxval": 80},
            },
        ],
        "float32": [
            {"addr": [33, 34], "value": 3124.5},
            {"addr": [35, 38], "value": 5678.19},
            {"addr": [39, 42], "value": 345000.18, "action": "increment"},
        ],
        "float64": [
            {"addr": [43, 46], "value": 4242.487},
            {"addr": [47, 50], "value": -1237.879, "action": "increment"},
        ],
        "string": [
            {"addr": [51, 52], "value": "Str"},
            {"addr": [53, 56], "value": "Strxyz12"},
        ],
        "repeat": [{"addr": [0, 56], "to": [57, 171]}],
    }

    default_server = {
        "server": {
            "comm": "tcp",
            "host": "test_host",
            "port": 5020,
            "ignore_missing_devices": False,
            "framer": "socket",
            "identity": {
                "VendorName": "pymodbus",
                "ProductCode": "PM",
                "VendorUrl": "https://github.com/pymodbus-dev/pymodbus/",
                "ProductName": "pymodbus Server",
                "ModelName": "pymodbus Server",
                "MajorMinorRevision": "3.1.0",
            },
        },
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
        Cell(
            type=CellType.UINT32,
            action=2,
            action_parameters={"minval": 10, "maxval": 80},
        ),
        Cell(type=CellType.NEXT, value=50),
        Cell(type=CellType.FLOAT32, access=True, value=17731),
        Cell(type=CellType.NEXT, access=True, value=18432),
        Cell(type=CellType.FLOAT32, access=True, value=17841),
        Cell(type=CellType.NEXT, access=True, value=29061),
        Cell(type=CellType.FLOAT32, access=True, value=17841),
        Cell(type=CellType.NEXT, access=True, value=29061),
        Cell(type=CellType.FLOAT32, value=18600, action=1),
        Cell(type=CellType.NEXT, value=29958),  # 40
        Cell(type=CellType.FLOAT32, value=18600, action=1),
        Cell(type=CellType.NEXT, value=29958),
        Cell(type=CellType.FLOAT64, access=True, value=16560),
        Cell(type=CellType.NEXT, access=True, value=37500),
        Cell(type=CellType.NEXT, access=True, value=44040),
        Cell(type=CellType.NEXT, access=True, value=12583),
        Cell(type=CellType.FLOAT64, value=49299, action=1),
        Cell(type=CellType.NEXT, value=22404),
        Cell(type=CellType.NEXT, value=6291),
        Cell(type=CellType.NEXT, value=29884),  # 50
        Cell(type=CellType.STRING, value=int.from_bytes(bytes("St", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("r ", "utf-8"), "big")),
        Cell(type=CellType.STRING, value=int.from_bytes(bytes("St", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("rx", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("yz", "utf-8"), "big")),
        Cell(type=CellType.NEXT, value=int.from_bytes(bytes("12", "utf-8"), "big")),
        # 48 MAX before repeat
    ]

    @classmethod
    def custom_action1(cls, _registers, _inx):
        """Test action."""

    @classmethod
    def custom_action2(cls, _registers, _inx):
        """Test action."""

    custom_actions = {
        "custom1": custom_action1,
        "custom2": custom_action2,
    }

    @pytest.fixture(name="device")
    def copy_default_device(self):
        """Copy default device."""
        return copy.deepcopy(self.default_device)

    @pytest.fixture(name="simulator")
    def create_simulator(self, device):
        """Create simulator context."""
        return ModbusSimulatorContext(device, self.custom_actions)

    def test_simulator_datastore(self, device):
        """Test object creation."""
        ModbusSimulatorContext(device, self.custom_actions)
        ModbusSimulatorContext(None, None)

    def test_pack_unpack_values(self):
        """Test the pack unpack methods."""
        value = 32145678
        regs = ModbusSimulatorContext.build_registers_from_value(value, CellType.UINT32)
        test_value = ModbusSimulatorContext.build_value_from_registers(
            regs, CellType.UINT32
        )
        assert value == test_value

        value = 3.14159265358979
        regs = ModbusSimulatorContext.build_registers_from_value(
            value, CellType.FLOAT32
        )
        test_value = ModbusSimulatorContext.build_value_from_registers(
            regs, CellType.FLOAT32
        )
        assert round(value, 6) == round(test_value, 6)

        value = 2.718281828459045
        regs = ModbusSimulatorContext.build_registers_from_value(
            value, CellType.FLOAT64
        )
        test_value = ModbusSimulatorContext.build_value_from_registers(
            regs, CellType.FLOAT64
        )
        assert round(value, 6) == round(test_value, 6)

    def test_simulator_config_verify(self, simulator):
        """Test basic configuration."""
        # Manually build expected memory image and then compare.
        assert simulator.register_count == 250
        for offset in (0, 57, 114):
            for i, test_cell in enumerate(self.test_registers):
                reg = simulator.registers[i + offset]
                assert reg.type == test_cell.type, f"at index {i} - {offset}"
                assert reg.access == test_cell.access, f"at index {i} - {offset}"
                assert reg.value == test_cell.value, f"at index {i} - {offset}"
                assert reg.action == test_cell.action, f"at index {i} - {offset}"
                assert reg.action_parameters == test_cell.action_parameters, (
                    f"at index {i} - {offset}"
                )
                assert reg.count_read == test_cell.count_read, (
                    f"at index {i} - {offset}"
                )
                assert reg.count_write == test_cell.count_write, (
                    f"at index {i} - {offset}"
                )

    def test_simulator_config_verify2(self, device):
        """Test basic configuration."""
        # Manually build expected memory image and then compare.
        device[Label.setup][Label.shared_blocks] = False
        device[Label.setup][Label.co_size] = 15
        device[Label.setup][Label.di_size] = 15
        device[Label.setup][Label.hr_size] = 15
        device[Label.setup][Label.ir_size] = 15
        del device[Label.repeat]
        device[Label.repeat] = []
        simulator = ModbusSimulatorContext(device, None)
        assert simulator.register_count == 60
        for i, test_cell in enumerate(self.test_registers):
            reg = simulator.registers[i]
            assert reg.type == test_cell.type, f"at index {i}"
            assert reg.value == test_cell.value, f"at index {i}"

    def test_simulator_invalid_config1(self, device):
        """Test exception for invalid configuration."""
        device["bad section"] = True
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    @pytest.mark.parametrize(
        ("entry"),
        [
            (Label.type_bits, 5),
            (Label.type_uint16, 16),
            (Label.type_uint32, [31, 32]),
            (Label.type_float32, [33, 34]),
            (Label.type_float64, [47, 50]),
            (Label.type_string, [51, 52]),
        ],
    )
    def test_simulator_invalid_config2(self, entry, device):
        """Test exception for invalid configuration."""
        device[entry[0]].append(entry[1])
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    def test_simulator_invalid_config3(self, device):
        """Test exception for invalid configuration."""
        del device[Label.type_bits]
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    def test_simulator_invalid_config4(self, device):
        """Test exception for invalid configuration."""
        device[Label.type_string][1][Label.value] = "very long string again"
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    def test_simulator_invalid_config5(self, device):
        """Test exception for invalid configuration."""
        device[Label.setup][Label.defaults][Label.action][Label.type_bits] = (
            "bad action"
        )
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    def test_simulator_invalid_config6(self, device):
        """Test exception for invalid configuration."""
        device[Label.invalid].append(700)
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    @pytest.mark.parametrize(("entry"), [700, 1])
    def test_simulator_invalid_config7(self, entry, device):
        """Test exception for invalid configuration."""
        device[Label.write].append(entry)
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    def test_simulator_invalid_config8(self, device):
        """Test exception for invalid configuration."""
        device[Label.type_bits].append(700)
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    def test_simulator_invalid_config9(self, device):
        """Test exception for invalid configuration."""
        device[Label.repeat][0][Label.repeat_to] = [48, 500]
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    def test_simulator_invalid_config10(self, device):
        """Test exception for invalid configuration."""
        device[Label.type_uint16].append(250)
        with pytest.raises(RuntimeError):
            ModbusSimulatorContext(device, None)

    async def test_simulator_get_values(self, simulator):
        """Test simulator get values."""
        for entry in (
            (FX_READ_BIT, 194, 1, [False]),
            (FX_READ_BIT, 83, 1, [True]),
            (FX_READ_BIT, 87, 5, [False] + [True] * 3 + [False]),
            (FX_READ_BIT, 198, 4, [True, False, True, True]),
            (FX_READ_REG, 19, 1, [14662]),
            (FX_READ_REG, 16, 2, [3124, 5678]),
        ):
            values = await simulator.async_OLD_getValues(entry[0], entry[1], entry[2])
            assert entry[3] == values, f"at entry {entry}"

    async def test_simulator_get_values_not(self, simulator):
        """Test simulator get values."""
        rc = await simulator.async_OLD_getValues(FX_READ_REG, 25000, 2)
        assert rc == ExcCodes.ILLEGAL_ADDRESS

    async def test_simulator_set_values(self, device):
        """Test simulator set values."""
        exc_simulator = ModbusSimulatorContext(device, None)
        value = [31234]
        await exc_simulator.async_OLD_setValues(FX_WRITE_REG, 16, value)
        result = await exc_simulator.async_OLD_getValues(FX_READ_REG, 16, 1)
        assert value == result
        value = [31234, 189]
        await exc_simulator.async_OLD_setValues(FX_WRITE_REG, 16, value)
        result = await exc_simulator.async_OLD_getValues(FX_READ_REG, 16, 2)
        assert value == result

        exc_simulator.registers[5].value = 0
        await exc_simulator.async_OLD_setValues(FX_WRITE_BIT, 80, [True])
        await exc_simulator.async_OLD_setValues(FX_WRITE_BIT, 82, [True])
        await exc_simulator.async_OLD_setValues(FX_WRITE_BIT, 84, [True])
        await exc_simulator.async_OLD_setValues(FX_WRITE_BIT, 86, [True, False, True])
        result = await exc_simulator.async_OLD_getValues(FX_READ_BIT, 80, 8)
        assert result == [True, False] * 4
        await exc_simulator.async_OLD_setValues(FX_WRITE_BIT, 88, [False])
        result = await exc_simulator.async_OLD_getValues(FX_READ_BIT, 86, 3)
        assert result == [True, False, False]
        await exc_simulator.async_OLD_setValues(FX_WRITE_BIT, 80, [True] * 17)

    async def test_simulator_set_values_not(self, device):
        """Test simulator set values."""
        exc_simulator = ModbusSimulatorContext(device, None)
        value = [31234]
        rc = await exc_simulator.async_OLD_setValues(FX_WRITE_REG, 5000, value)
        assert rc == ExcCodes.ILLEGAL_ADDRESS
        rc = await exc_simulator.async_OLD_setValues(FX_WRITE_BIT, 5000, value)
        assert rc == ExcCodes.ILLEGAL_ADDRESS

    def test_simulator_get_text(self, simulator):
        """Test get_text_register()."""
        for test_reg, test_entry, test_cell in (
            (1, "1", Cell(type=Label.invalid, action="none", value="0")),
            (5, "5", Cell(type=Label.type_bits, action="none", value="0x708")),
            (
                31,
                "31-32",
                Cell(
                    type=Label.type_uint32,
                    action="random({'minval': 10, 'maxval': 80})",
                    value="50",
                ),
            ),
            (33, "33-34", Cell(type=Label.type_float32, action="none", value="3124.5")),
            (
                47,
                "47-50",
                Cell(type=Label.type_float64, action="increment", value="-1237.879"),
            ),
            (51, "51-52", Cell(type=Label.type_string, action="none", value="Str ")),
        ):
            reg = simulator.registers[test_reg]
            entry, cell = simulator.get_text_register(test_reg)
            assert entry == test_entry, f"at register {test_reg}"
            assert cell.type == test_cell.type, f"at register {test_reg}"
            assert cell.access == str(reg.access), f"at register {test_reg}"
            assert cell.value == test_cell.value, f"at register {test_reg}"
            assert cell.action == test_cell.action, f"at register {test_reg}"
            assert cell.count_read == str(reg.count_read), f"at register {test_reg}"
            assert cell.count_write == str(reg.count_write), f"at register {test_reg}"

    @pytest.mark.parametrize(
        ("func", "addr"),
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
    async def test_simulator_actions(self, func, addr, action, device):
        """Test actions."""
        exc_simulator = ModbusSimulatorContext(device, None)
        reg1 = exc_simulator.registers[addr]
        reg2 = exc_simulator.registers[addr + 1]
        reg1.action = exc_simulator.action_name_to_id[action]
        reg1.value = 0
        reg2.value = 0
        if func == FX_READ_BIT:
            addr = addr * 16 - 16 + 14
        values = await exc_simulator.async_OLD_getValues(func, addr, 2)
        assert values[0] or values[1]

    async def test_simulator_action_timestamp(self, device):
        """Test action timestamp."""
        exc_simulator = ModbusSimulatorContext(device, None)
        addr = 12
        exc_simulator.registers[addr].action = exc_simulator.action_name_to_id[
            Label.timestamp
        ]
        await exc_simulator.async_OLD_getValues(FX_READ_REG, addr, 1)

    async def test_simulator_action_reset(self, device):
        """Test action reset."""
        exc_simulator = ModbusSimulatorContext(device, None)
        addr = 12
        exc_simulator.registers[addr].action = exc_simulator.action_name_to_id[
            Label.reset
        ]
        with pytest.raises(RuntimeError):
            await exc_simulator.async_OLD_getValues(FX_READ_REG, addr, 1)

    @pytest.mark.parametrize(
        ("celltype", "minval", "maxval", "value", "expected"),
        [
            (CellType.BITS, 50, 75, 73, (74, 75, 50)),
            (CellType.BITS, 50, 75, 45, (50, 51, 52)),
            (CellType.UINT16, 50, 15075, 15073, (15074, 15075, 50)),
            (CellType.UINT16, 50, 75, 45, (50, 51, 52)),
            (CellType.UINT32, 50, 63075, 63073, (63074, 63075, 50)),
            (CellType.UINT32, 50, 75, 45, (50, 51, 52)),
            (CellType.FLOAT32, 27.0, 16100.5, 16098.0, (16099.0, 16100.0, 27.0)),
            (CellType.FLOAT32, 27.0, 75.5, 24.0, (27.0, 28.0, 29.0)),
            (CellType.FLOAT64, 27.0, 1615, 24.0, (27.0, 28.0, 29.0)),
            (CellType.FLOAT64, -29.5, 75.5, -40, (-29.5, -28.5, -27.5)),
        ],
    )
    async def test_simulator_action_increment(
        self, celltype, minval, maxval, value, expected, device
    ):
        """Test action increment."""
        exc_simulator = ModbusSimulatorContext(device, None)
        action = exc_simulator.action_name_to_id[Label.increment]
        parameters = {
            "minval": minval,
            "maxval": maxval,
        }
        exc_simulator.registers[30].type = celltype.value
        exc_simulator.registers[30].action = action
        exc_simulator.registers[30].action_parameters = parameters
        for i in range(3):
            exc_simulator.registers[31 + i].type = CellType.NEXT
            exc_simulator.registers[31 + i].action = 0

        regs = ModbusSimulatorContext.build_registers_from_value(value, celltype)
        reg_count = CellType.register_count(celltype)

        for i, new_value in enumerate(regs):
            exc_simulator.registers[30 + i].value = new_value

        for expect_value in expected:
            if celltype != CellType.BITS:
                regs = await exc_simulator.async_OLD_getValues(
                    FX_READ_REG, 30, reg_count
                )
                reg_value = ModbusSimulatorContext.build_value_from_registers(
                    regs, celltype
                )

            else:
                reg_bits = await exc_simulator.async_OLD_getValues(
                    FX_READ_BIT, 30 * 16, 16
                )
                reg_value = sum(bit * 2**i for i, bit in enumerate(reg_bits))

            assert expect_value == reg_value, f"type({CellType(celltype).name})"

    @pytest.mark.parametrize(
        ("celltype", "minval", "maxval"),
        [
            (CellType.BITS, 50, 75),
            (CellType.UINT16, 50, 15075),
            (CellType.UINT32, 50, 63075),
            (CellType.FLOAT32, 27.0, 16100.5),
            (CellType.FLOAT32, 65.0, 78.0),
            (CellType.FLOAT64, 78.5, 124.3),
            (CellType.FLOAT64, 125.7, 354.2),
        ],
    )
    async def test_simulator_action_random(self, celltype, minval, maxval, device):
        """Test action random."""
        exc_simulator = ModbusSimulatorContext(device, None)
        action = exc_simulator.action_name_to_id[Label.random]
        parameters = {
            "minval": minval,
            "maxval": maxval,
        }
        exc_simulator.registers[30].type = celltype
        exc_simulator.registers[30].action = action
        exc_simulator.registers[30].action_parameters = parameters
        exc_simulator.registers[31].type = CellType.NEXT
        exc_simulator.registers[31].action = 0
        reg_count = CellType.register_count(celltype)
        for _i in range(100):
            if celltype != CellType.BITS:
                regs = await exc_simulator.async_OLD_getValues(
                    FX_READ_REG, 30, reg_count
                )
            else:
                reg_bits = await exc_simulator.async_OLD_getValues(
                    FX_READ_BIT, 30 * 16, 16
                )
                reg_value = sum(bit * 2**i for i, bit in enumerate(reg_bits))
                regs = [reg_value]
            if reg_count == 1:
                new_value = regs[0]
            else:
                new_value = ModbusSimulatorContext.build_value_from_registers(
                    regs, celltype
                )
            assert minval <= new_value <= maxval

    def test_simulator_loop_validate(self, simulator):
        """Test simulator set values."""
        assert not simulator.loop_validate(59, 60, False)
        simulator.type_exception = True
        assert simulator.loop_validate(5, 6, False)
        assert not simulator.loop_validate(46, 47, False)
        assert simulator.loop_validate(51, 53, False)
        assert not simulator.loop_validate(45, 50, False)
        assert not simulator.loop_validate(21, 22, False)
        assert simulator.loop_validate(21, 23, False)

    @pytest.mark.parametrize(
        ("celltype", "count", "is_int", "is_64"),
        [
            (CellType.INVALID, -1, False, False),
            (CellType.BITS, 1, True, False),
            (CellType.UINT16, 1, True, False),
            (CellType.UINT32, 2, True, False),
            (CellType.FLOAT32, 2, False, False),
            (CellType.FLOAT64, 4, False, True),
            (CellType.STRING, -1, False, False),
            (CellType.NEXT, -1, False, False),
        ],
    )
    def test_cell_type(self, celltype: CellType, count: int, is_int: bool, is_64: bool):
        """Test CellType methods."""
        if count < 0:
            with pytest.raises(RuntimeError):
                CellType.register_count(celltype)
        else:
            assert CellType.register_count(celltype) == count

        assert CellType.is_int(celltype) == is_int
        assert CellType.is_64(celltype) == is_64
