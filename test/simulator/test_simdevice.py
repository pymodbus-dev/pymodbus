"""Test SimDevice."""


import pytest

from pymodbus import ModbusDeviceIdentification
from pymodbus.constants import DataType, RuntimeFlags
from pymodbus.simulator import SimData, SimDevice


class TestSimDevice:
    """Test simulator device config."""

    async def my_action(
            self,
            _function_code,
            _address,
            current_registers,
            _new_registers
        ):
        """Run action."""
        return current_registers

    def my_sync_action(
            self,
            _function_code,
            _address,
            current_registers,
            _new_registers
        ):
        """Run action."""
        return current_registers

    simdata1 = SimData(0, datatype=DataType.INT16, values=15)
    simdata2 = SimData(1, datatype=DataType.INT16, values=16)
    simdata3 = SimData(1, datatype=DataType.BITS, values=16)

    @pytest.mark.parametrize("kwargs", [
        {"id": 0, "simdata": [SimData(2, datatype=DataType.STRING, values="test")], "string_encoding": "utf-8"},
        {"id": 0, "simdata": ([simdata3], [simdata3], [simdata1], [simdata3])},
        {"id": 0, "simdata": [simdata2, simdata1]},
        {"id": 0, "type_check": True, "simdata": [simdata1]},
        {"id": 0, "simdata": [simdata1], "endian": (False, True)},
        {"id": 0, "simdata": [simdata1], "endian": (True, False)},
        {"id": 0, "simdata": [simdata1], "identity": ModbusDeviceIdentification()},
    ])
    def test_simdevice_instanciate(self, kwargs):
        """Test that simdata can be objects."""
        SimDevice(**kwargs)

    @pytest.mark.parametrize("kwargs", [
        {"id": 0},
        {"id": 0, "simdata": [simdata1], "identity": 123},
        {"simdata": []},
        {"id": 0, "simdata": (simdata3, [simdata3], [simdata1], [simdata3])},
        {"id": 0, "simdata": (["not ok"], [simdata3], [simdata1], [simdata3])},
        {"id": 0, "simdata": ([simdata1], [simdata3], [simdata1], [simdata1])},
        {"id": 0, "simdata": ([simdata3], [simdata1], [simdata1], [simdata1])},
        {"id": 0, "simdata": ([simdata3], [simdata3], [simdata1], "not ok")},
        {"id": 0, "simdata": [simdata1], "string_encoding": "not ok"},
        {"id": "not ok", "simdata": [simdata1]},
        {"id": 1.0, "simdata": [simdata1]},
        {"id": 1, "simdata": [simdata1, simdata1]},
        {"id": 256, "simdata": [simdata1]},
        {"id": -1, "simdata": [simdata1]},
        {"id": 1, "simdata": [simdata1], "word_order_big": "hmm"},
        {"id": 1, "simdata": [simdata1], "byte_order_big": "hmm"},
        {"id": 0, "simdata": [simdata1], "type_check": "hmm"},
        {"id": 0, "simdata": ["not ok"]},
        {"id": 0, "simdata": SimData(1, datatype=DataType.INT16, values=3)},
    ])
    def test_simdevice_not_ok(self, kwargs):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(**kwargs)

    @pytest.mark.parametrize(("block", "expect"), [
        ([SimData(0, values=0xffff, datatype=DataType.BITS)], 0),
        ([SimData(0, values=[0xffff], datatype=DataType.BITS)], 0),
        ([SimData(0, values=[True], datatype=DataType.BITS)], 0),
        ([SimData(0, values="hello", datatype=DataType.STRING)], 0),
        (SimData(0), 2),
        ("no valid", 2),
        (["no valid"], 2),
    ])
    def test_simdevice_block(self, block, expect):
        """Test that simdata can be objects."""
        if not expect:
            SimDevice(id=0, simdata=block)
        else: # expect == 2:
            with pytest.raises(TypeError):
                SimDevice(id=0, simdata=block)

    @pytest.mark.parametrize(("endian", "expect"), [
        ("not ok", 1),
        (None, 1),
        (["not ok"], 1),
        (("not ok"), 1),  # noqa: PT014
        (("not ok", "not_ok"), 1),
        ((True, False), 0),
    ])
    def test_simdevice_endian(self, endian, expect):
        """Test offset."""
        if expect:
            with pytest.raises(TypeError):
                SimDevice(id=0, simdata=[self.simdata1], endian=endian)
        else:
            SimDevice(id=0, simdata=[self.simdata1], endian=endian)

    async def test_simdevice_action(self):
        """Test action."""
        await self.my_action(0, 0, [], None)
        self.my_sync_action(0, 0, [], None)
        SimDevice(1, simdata=[SimData(1)], action=self.my_action)
        with pytest.raises(TypeError):
            SimDevice(1, simdata=[SimData(1)], action=self.my_sync_action)
        with pytest.raises(TypeError):
            SimDevice(1, simdata=[SimData(1)], action="no good")

    @pytest.mark.parametrize(("block", "result"), [
        ([SimData(1, values=123, readonly=True, datatype=DataType.INT16)],
         (1, [123],
            [RuntimeFlags.REG_SIZE_1 | RuntimeFlags.READONLY])),
        ([SimData(1, values="ABC", datatype=DataType.STRING)],
         (1, [0x4142, 0x4300],
            [RuntimeFlags.REG_SIZE_1, RuntimeFlags.REG_SIZE_1 | RuntimeFlags.REG_NEXT])),
        ([SimData(0, values=0xffff, datatype=DataType.BITS)], (0, [65535], [RuntimeFlags.REG_SIZE_1])),
        ([SimData(0, values=[0xffff, 0xffff], datatype=DataType.BITS)],
         (0, [65535, 65535], [RuntimeFlags.REG_SIZE_1, RuntimeFlags.REG_SIZE_1 | RuntimeFlags.REG_NEXT])),
        ([SimData(1, values=123, datatype=DataType.INT16),
            SimData(3, values=456, datatype=DataType.INT16)],
         (1, [123, 0, 456],
            [RuntimeFlags.REG_SIZE_1, RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID, RuntimeFlags.REG_SIZE_1])),
        ([SimData(1, values=123, datatype=DataType.REGISTERS),
            SimData(3, values=456, datatype=DataType.REGISTERS)],
         (1, [123, 0, 456],
            [RuntimeFlags.REG_SIZE_1, RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID, RuntimeFlags.REG_SIZE_1])),
        ([SimData(1, datatype=DataType.INVALID),
            SimData(3, datatype=DataType.INVALID)],
         (1, [0, 0, 0],
            [RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID, RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID, RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID])),
        ([SimData(0, values=123, datatype=DataType.INT32),
          SimData(3, values=456, datatype=DataType.INT32)],
          (0, [0, 123, 0, 0, 456], [RuntimeFlags.REG_SIZE_2,
                                 RuntimeFlags.REG_SIZE_2 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID,
                                 RuntimeFlags.REG_SIZE_2,
                                 RuntimeFlags.REG_SIZE_2 | RuntimeFlags.REG_NEXT])),
        ([SimData(0, values=123, datatype=DataType.UINT32),
          SimData(3, values=456, datatype=DataType.UINT32)],
          (0, [0, 123, 0, 0, 456], [RuntimeFlags.REG_SIZE_2,
                                 RuntimeFlags.REG_SIZE_2 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID,
                                 RuntimeFlags.REG_SIZE_2,
                                 RuntimeFlags.REG_SIZE_2 | RuntimeFlags.REG_NEXT])),
        ([SimData(0, values=27123.5, datatype=DataType.FLOAT32),
          SimData(3, values=-3.141592, datatype=DataType.FLOAT32)],
          (0, [0x46D3, 0xE700, 0, 0xC049, 0x0FD8], [RuntimeFlags.REG_SIZE_2,
                                 RuntimeFlags.REG_SIZE_2 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID,
                                 RuntimeFlags.REG_SIZE_2,
                                 RuntimeFlags.REG_SIZE_2 | RuntimeFlags.REG_NEXT])),
        ([SimData(0, values=-1234567890123456789, datatype=DataType.INT64),
          SimData(5, values=1234567890123456789, datatype=DataType.INT64)],
          (0, [0xEEDD, 0xEF0B, 0x8216, 0x7EEB, 0, 0x1122, 0x10F4, 0x7DE9, 0x8115], [RuntimeFlags.REG_SIZE_4,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID,
                                 RuntimeFlags.REG_SIZE_4,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT])),
        ([SimData(0, values=1234567890123456789, datatype=DataType.UINT64),
          SimData(5, values=1234567890123456789, datatype=DataType.UINT64)],
          (0, [0x1122, 0x10F4, 0x7DE9, 0x8115, 0, 0x1122, 0x10F4, 0x7DE9, 0x8115], [RuntimeFlags.REG_SIZE_4,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID,
                                 RuntimeFlags.REG_SIZE_4,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT])),
        ([SimData(0, values=3.14159265358979, datatype=DataType.FLOAT64),
          SimData(5, values=-3.14159265358979, datatype=DataType.FLOAT64)],
          (0, [0x4009, 0x21FB, 0x5444, 0x2D11, 0, 0xC009, 0x21FB, 0x5444, 0x2D11], [RuntimeFlags.REG_SIZE_4,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_1 | RuntimeFlags.INVALID,
                                 RuntimeFlags.REG_SIZE_4,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT,
                                 RuntimeFlags.REG_SIZE_4 | RuntimeFlags.REG_NEXT])),
        (([SimData(1, values=123, datatype=DataType.BITS)], [SimData(1, values=123, datatype=DataType.BITS)],
           [SimData(1, values=123, datatype=DataType.INT16)], [SimData(1, values=123, datatype=DataType.INT16)]),
         (((1, [123], [RuntimeFlags.REG_SIZE_1]), (1, [123], [RuntimeFlags.REG_SIZE_1]),
           (1, [123], [RuntimeFlags.REG_SIZE_1]), (1, [123], [RuntimeFlags.REG_SIZE_1])))),
        ])
    def test_simdevice_build(self, block, result):
        """Test build_device() ok."""
        sd = SimDevice(id=1, simdata=block)
        lists = sd.build_device()
        assert lists[0] == result[0]
        assert lists[1] == result[1]
