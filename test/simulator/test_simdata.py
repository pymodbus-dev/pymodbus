"""Test SimData."""
import pytest

from pymodbus.simulator import DataType, SimData


class TestSimData:
    """Test simulator data config."""

    @pytest.mark.parametrize("kwargs", [
        {"address": 0},
        {"address": 65535},
        {"address": 65535, "count": 1},
        {"address": 0, "count": 65536},
        {"address": 1, "count": 65535},
        {"address": 1, "count": 10, "datatype": DataType.INVALID},
        {"address": 3, "count": 10, "readonly": True},
        {"address": 4, "datatype": DataType.INT16, "values": 17},
        {"address": 5, "datatype": DataType.INT16, "values": [17, 18]},
        {"address": 6, "count": 10, "datatype": DataType.INT16, "values": [17, 18]},
        {"address": 7, "datatype": DataType.STRING, "values": "test"},
        {"address": 8, "count": 10, "datatype": DataType.STRING, "values": "test"},
        {"address": 8, "count": 10, "datatype": DataType.STRING, "values": "test", "string_encoding": "utf-8"},
        {"address": 0, "datatype": DataType.REGISTERS, "values": 17, "count": 5},
        {"address": 3, "datatype": DataType.INT16, "values": 17, "readonly": True},
        {"address": 0, "count": 2^16 -1},
        {"address": 4, "datatype": DataType.BITS, "values": True},
        {"address": 4, "datatype": DataType.BITS, "values": [True, True]},
    ])
    def test_simdata_instanciate(self, kwargs):
        """Test that simdata can be objects."""
        SimData(**kwargs)

    @pytest.mark.parametrize("kwargs", [
        {"address": "not ok"},
        {"address": 1.0},
        {"address": -1},
        {"address": 70000},
        {"address": 1, "count": 65537},
        {"address": 65535, "count": 2},
        {"address": 1, "count": "not ok"},
        {"address": 1, "count": 1.0},
        {"address": 1, "count": -1},
        {"address": 1, "count": 70000},
        {"address": 1, "count": 0},
        {"address": 1, "datatype": "not ok"},
        {"address": 1, "datatype": 11},
        {"address": 2, "values": 17},
        {"address": 8, "count": 10, "datatype": DataType.STRING, "values": "test", "string_encoding": "not ok"},
    ])
    def test_simdata_not_ok(self, kwargs):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimData(**kwargs)

    @pytest.mark.parametrize(("value", "value_type"), [
        ("ok str", DataType.STRING),
        (["ok str", "ok2"], DataType.STRING),
        (1.0, DataType.FLOAT32),
        ([1.0, 2.0], DataType.FLOAT32),
        (1, DataType.INT32),
        ([1, 2], DataType.INT32),
        (11, DataType.REGISTERS),
        ([11, 12], DataType.REGISTERS),
        (True, DataType.BITS),
        ([True, False], DataType.BITS),
        ])
    def test_simdata_value_ok(self, value, value_type):
        """Test simdata value."""
        SimData(0, values=value, datatype=value_type)

    @pytest.mark.parametrize(("value", "value_type"), [
        (1, DataType.STRING),
        ("", DataType.STRING),
        (1, DataType.FLOAT32),
        ([], DataType.INT16),
        ([1.0, 2], DataType.FLOAT32),
        (1.0, DataType.INT32),
        ([1, 2.0], DataType.INT32),
        ("not ok", DataType.REGISTERS),
        (1.0, DataType.REGISTERS),
        ([11, 12.0], DataType.REGISTERS),
        (1.0, DataType.BITS),
        ([True, 1.0], DataType.BITS),
        ([True, 1], DataType.BITS),
        ([1, True], DataType.BITS),
        ])
    def test_simdata_value_not_ok(self, value, value_type):
        """Test simdata value."""
        with pytest.raises(TypeError):
            SimData(0, values=value, datatype=value_type)

    @pytest.mark.parametrize(("values"), [1, [1, 2] ])
    def test_simdata_value_invalid(self, values):
        """Test invalid."""
        with pytest.raises(TypeError):
            SimData(0, values=values, datatype=DataType.INVALID)

    @pytest.mark.parametrize(("value", "value_type", "regs"), [
        (27123, DataType.INT16, [27123]),
        (-27123, DataType.INT16, [0x960d]),
        ([-27123, 27123], DataType.INT16, [0x960D, 0x69F3]),
        ([32145678, -32145678], DataType.INT32, [0x01EA, 0x810E, 0xFE15, 0x7EF2]),
        (27123, DataType.REGISTERS, [0x69F3]),
        (-27124, DataType.INT16, [0x960C]),
        (27123, DataType.UINT16, [0x69F3]),
        (-32145678, DataType.INT32, [0xFE15, 0x7EF2]),
        (32145678, DataType.UINT32, [0x01EA, 0x810E]),
        (-1234567890123456789, DataType.INT64, [0xEEDD, 0xEF0B, 0x8216, 0x7EEB]),
        (1234567890123456789, DataType.UINT64, [0x1122, 0x10F4, 0x7DE9, 0x8115]),
        (27123.5, DataType.FLOAT32, [0x46D3, 0xE700]),
        (3.141592, DataType.FLOAT32, [0x4049, 0x0FD8]),
        (-3.141592, DataType.FLOAT32, [0xC049, 0x0FD8]),
        (27123.5, DataType.FLOAT64, [0x40DA, 0x7CE0, 0x0000, 0x0000]),
        (3.14159265358979, DataType.FLOAT64, [0x4009, 0x21FB, 0x5444, 0x2D11]),
        (-3.14159265358979, DataType.FLOAT64, [0xC009, 0x21FB, 0x5444, 0x2D11]),
        (0x0100, DataType.BITS, [256]),
        (123, DataType.BITS, [123]),
        ([123], DataType.BITS, [123]),
        ([0x0100, 0x0001], DataType.BITS, [256, 1]),
        ([True] + [False] * 15, DataType.BITS, [1]),
        ([True] + [False] * 8 + [True] + [False] * 6, DataType.BITS, [513]),
        ([True] + [False] * 15 + [False] * 8 + [True] + [False] * 7, DataType.BITS, [1, 256]),
        ])
    def test_simdata_build_registers(self, value, value_type, regs):
        """Test simdata value."""
        sd = SimData(0, values=value, datatype=value_type)
        build_regs = sd.build_registers(False)
        assert build_regs == regs

    @pytest.mark.parametrize(("value", "code", "expect"), [
        ("ABC", "utf-8", [0x4142, 0x4300]),
        ("abcdÇ", "utf-8", [0x6162, 0x6364, 0xc387]),
        ("abcdÇ", "cp437", [0x6162, 0x6364, 0x8000]),
        (["ABC", "DEFG"], "utf-8", [0x4142, 0x4300,0x4445, 0x4647]),
        ])
    def test_simdata_build_string(self, value, code, expect):
        """Test simdata value."""
        sd = SimData(0, values=value, datatype=DataType.STRING, string_encoding=code)
        build_regs = sd.build_registers(False)
        assert build_regs == expect

    @pytest.mark.parametrize(("value", "regs"), [
        ([True, False, True], [True, False, True]),
        ([True] + [False] * 14 + [True, False], [True] + [False] * 14 + [True, False]),
        (0x0001, [True] + [False]*15),
        (0x0100, [False]*8 + [True] + [False]*7),
        ([256, 1], [False]*8 + [True] + [False]*7 + [True] + [False]*15),
        ])
    def test_simdata_build_bit_block(self, value, regs):
        """Test simdata value."""
        sd = SimData(0, values=value, datatype=DataType.BITS)
        build_regs = sd.build_registers(True)
        assert build_regs == regs

    def test_simdata_build_updated_simdata(self):
        """Test simdata value."""
        sd = SimData(0, values="ABC", datatype=DataType.STRING)
        build_regs = sd.build_registers(False)
        assert build_regs == [0x4142, 0x4300]
        sd.values="ABCDEF"
        build_regs = sd.build_registers(False)
        assert build_regs == [0x4142, 0x4344, 0x4546]

        sd.values=123
        with pytest.raises(TypeError):
            sd.build_registers(False)
        sd = SimData(0, values=[True, True], datatype=DataType.BITS)
        with pytest.raises(TypeError):
            sd.build_registers(False)

