"""Test SimDevice."""
from typing import cast

import pytest

from pymodbus import ModbusDeviceIdentification
from pymodbus.simulator import DataType, SimData, SimDevice
from pymodbus.simulator.simdevice import SimRegs
from pymodbus.simulator.simruntime import SimUtils


class TestSimDevice:
    """Test simulator device config."""

    async def my_action(
            self,
            _function_code,
            _start_address,
            _address,
            _count,
            _current_registers,
            _set_values
        ):
        """Run action."""

    def my_sync_action(
            self,
            _function_code,
            _start_address,
            _address,
            _count,
            _current_registers,
            _set_values
        ):
        """Run action."""

    simdata1 = SimData(0, datatype=DataType.INT16, values=15)
    simdata2 = SimData(1, datatype=DataType.INT16, values=16)
    simdata3 = SimData(10, datatype=DataType.BITS, values=16)

    @pytest.mark.parametrize("kwargs", [
        {"id": 0, "simdata": [SimData(2, datatype=DataType.STRING, values="test")]},
        {"id": 0, "simdata": ([simdata3], [simdata3], [simdata1], [simdata3])},
        {"id": 0, "simdata": simdata2},
        {"id": 0, "simdata": [simdata2, simdata1]},
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
        {"id": 0, "simdata": ([simdata3], [simdata1], [simdata3])},
        {"id": 0, "simdata": (["not ok"], [simdata3], [simdata1], [simdata3])},
        {"id": 0, "simdata": ([simdata1], [simdata3], [simdata1], [simdata1])},
        {"id": 0, "simdata": ([simdata3], [simdata1], [simdata1], [simdata1])},
        {"id": 0, "simdata": ([simdata3], [simdata3], [simdata1], "not ok")},
        {"id": "not ok", "simdata": [simdata1]},
        {"id": 1.0, "simdata": [simdata1]},
        {"id": 1, "simdata": [simdata1, simdata1]},
        {"id": 256, "simdata": [simdata1]},
        {"id": -1, "simdata": [simdata1]},
        {"id": 1, "simdata": [simdata1], "word_order_big": "hmm"},
        {"id": 1, "simdata": [simdata1], "byte_order_big": "hmm"},
        {"id": 0, "simdata": ["not ok"]},
    ])
    def test_simdevice_not_ok(self, kwargs):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(**kwargs)

    @pytest.mark.parametrize(("block", "expect"), [
        ([SimData(0, values=0xffff, datatype=DataType.BITS)], 0),
        ([SimData(0, values=[0xffff], datatype=DataType.BITS)], 0),
        ([SimData(0, values=[True]*16, datatype=DataType.BITS)], 0),
        ([SimData(0, values="hello", datatype=DataType.STRING)], 0),
        # (SimData(0), 0),
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

    async def test_simdevice_action(self):
        """Test action."""
        await self.my_action(0, 0, 0, 0, [], None)
        self.my_sync_action(0, 0, 0, 0, [], None)
        SimDevice(1, simdata=[SimData(1)], action=self.my_action)
        SimDevice(0, simdata=([self.simdata3], [self.simdata3], [self.simdata1], [self.simdata3]), action=self.my_action)
        with pytest.raises(TypeError):
            SimDevice(1, simdata=[SimData(1)], action=self.my_sync_action)
        with pytest.raises(TypeError):
            SimDevice(1, simdata=[SimData(1)], action="no good")  # type: ignore[arg-type]

    async def test_simdevice_bit_addressing(self):
        """Test action."""
        sdblock = ([self.simdata3], [self.simdata3], [self.simdata1], [self.simdata3])
        SimDevice(1, simdata=[SimData(1)], use_bit_addressing=False)
        SimDevice(1, simdata=[SimData(1)], use_bit_addressing=True)
        SimDevice(1, simdata=sdblock, use_bit_addressing=True)
        with pytest.raises(TypeError):
            SimDevice(1, simdata=sdblock, use_bit_addressing=False)

    @pytest.mark.parametrize(("block", "result"), [
        ([SimData(2, values=125, datatype=DataType.REGISTERS), SimData(1, values=123, datatype=DataType.REGISTERS),],
         (1, [123, 125, 0],
            [DataType.INT16, DataType.INT16, DataType.INVALID])),
        ([SimData(1, values=123, readonly=True, datatype=DataType.INT16)],
         (1, [123, 0],
            [DataType.INT16 | SimUtils.RunTimeFlag_READONLY, DataType.INVALID])),
        ([SimData(1, values="ABC", datatype=DataType.STRING)],
         (1, [0x4142, 0x4300, 0],
            [DataType.STRING, 0, DataType.INVALID])),
        ([SimData(1, values="ABC", datatype=DataType.STRING), SimData(3, values="ABC", datatype=DataType.STRING)],
         (1, [0x4142, 0x4300, 0x4142, 0x4300,0],
            [DataType.STRING, 0, DataType.STRING, 0, DataType.INVALID])),
        ([SimData(0, values=0xffff, datatype=DataType.BITS)],
         (0, [65535, 0],
            [DataType.BITS, DataType.INVALID])),
        ([SimData(0, values=[0xffff, 0xffff], datatype=DataType.BITS)],
         (0, [65535, 65535, 0],
            [DataType.BITS, 0, DataType.INVALID])),
        ([SimData(0, values=[True] * 2 + [False]*6 + [False]*8, datatype=DataType.BITS)],
         (0, [3, 0],
            [DataType.BITS, DataType.INVALID])),
        ([SimData(0, values=[True] * 2 + [False]*6 + [True]  + [False]*6 + [True], datatype=DataType.BITS)],
         (0, [33027, 0],
            [DataType.BITS, DataType.INVALID])),
        ([SimData(1, values=123, datatype=DataType.INT16),
            SimData(3, values=456, datatype=DataType.INT16)],
         (1, [123, 0, 456, 0],
            [DataType.INT16, DataType.INVALID, DataType.INT16, DataType.INVALID])),
        ([SimData(1, values=123, datatype=DataType.REGISTERS),
            SimData(3, values=456, datatype=DataType.REGISTERS)],
         (1, [123, 0, 456, 0],
            [DataType.REGISTERS, DataType.INVALID, DataType.REGISTERS, DataType.INVALID])),
        ([SimData(1, datatype=DataType.INVALID),
            SimData(3, datatype=DataType.INVALID)],
         (1, [0, 0, 0, 0],
            [DataType.INVALID, DataType.INVALID, DataType.INVALID, DataType.INVALID])),
        ([SimData(0, values=123, datatype=DataType.INT32),
          SimData(3, values=456, datatype=DataType.INT32)],
          (0, [0, 123, 0, 0, 456, 0],
           [DataType.INT32, 0, DataType.INVALID, DataType.INT32, 0, DataType.INVALID])),
        ([SimData(0, values=123, datatype=DataType.INT32),
          SimData(2, values=456, datatype=DataType.INT32)],
          (0, [0, 123, 0, 456, 0],
           [DataType.INT32, 0, DataType.INT32, 0, DataType.INVALID])),
        ([SimData(0, values=123, datatype=DataType.UINT32),
          SimData(3, values=456, datatype=DataType.UINT32)],
          (0, [0, 123, 0, 0, 456, 0],
           [DataType.UINT32, 0, DataType.INVALID, DataType.UINT32, 0, DataType.INVALID])),
        ([SimData(0, values=27123.5, datatype=DataType.FLOAT32),
          SimData(3, values=-3.141592, datatype=DataType.FLOAT32)],
          (0, [0x46D3, 0xE700, 0, 0xC049, 0x0FD8, 0],
            [DataType.FLOAT32, 0, DataType.INVALID, DataType.FLOAT32, 0, DataType.INVALID])),
        ([SimData(0, values=-1234567890123456789, datatype=DataType.INT64),
          SimData(5, values=1234567890123456789, datatype=DataType.INT64)],
          (0, [0xEEDD, 0xEF0B, 0x8216, 0x7EEB, 0, 0x1122, 0x10F4, 0x7DE9, 0x8115, 0],
            [DataType.INT64, 0, 0, 0, DataType.INVALID, DataType.INT64, 0, 0, 0, DataType.INVALID])),
        ([SimData(0, values=1234567890123456789, datatype=DataType.UINT64),
          SimData(5, values=1234567890123456789, datatype=DataType.UINT64)],
          (0, [0x1122, 0x10F4, 0x7DE9, 0x8115, 0, 0x1122, 0x10F4, 0x7DE9, 0x8115, 0],
            [DataType.UINT64, 0, 0, 0, DataType.INVALID, DataType.UINT64, 0, 0, 0, DataType.INVALID])),
        ([SimData(0, values=3.14159265358979, datatype=DataType.FLOAT64),
          SimData(5, values=-3.14159265358979, datatype=DataType.FLOAT64)],
          (0, [0x4009, 0x21FB, 0x5444, 0x2D11, 0, 0xC009, 0x21FB, 0x5444, 0x2D11, 0],
            [DataType.FLOAT64, 0, 0, 0, DataType.INVALID, DataType.FLOAT64, 0, 0, 0, DataType.INVALID])),
        ])
    def test_simdevice_build(self, block, result):
        """Test build_device() ok."""
        sd = SimDevice(id=1, simdata=block)
        lists = sd.build_device()
        assert cast(tuple, lists)[0] == result[0]
        assert cast(tuple, lists)[1] == result[1]

    def test_simdevice_build_blocks(self):
        """Test build_device() ok."""
        block = (
            [SimData(0, values=123, datatype=DataType.BITS)],
            [SimData(0, values=123, readonly=True, datatype=DataType.BITS)],
            [SimData(0, values=123, datatype=DataType.INT16)],
            [SimData(0, values=123, datatype=DataType.INT16)])
        result = {
            "c": (0, [123, 0], [DataType.BITS, DataType.INVALID]),
            "d": (0, [123, 0], [DataType.BITS, DataType.INVALID]),
            "h": (0, [123, 0], [DataType.INT16, DataType.INVALID]),
            "i": (0, [123,0], [DataType.INT16, DataType.INVALID])
        }
        sd = SimDevice(id=1, simdata=block)
        lists = sd.build_device()
        assert lists == result

    @pytest.mark.parametrize(("block", "registers", "addr"), [
        ([SimData(0, values=123, datatype=DataType.BITS)], [0x007b, 0x0000], 0),
        ([SimData(0, values=True, datatype=DataType.BITS)], [0x0001, 0x0000], 0),
        ([SimData(1, values=123, datatype=DataType.BITS)], [0x00F6, 0x0000, 0x0000], 0),
        ([SimData(0, values=[True] + [False]*7, datatype=DataType.BITS),
          SimData(9, values=[True], datatype=DataType.BITS)], [0x0201, 0x0000], 0),
        ([SimData(0, values=[True] + [False]*7, datatype=DataType.BITS),
          SimData(10, values=[True], datatype=DataType.BITS)], [0x0401, 0x0000], 0),
        ([SimData(16, values=123, datatype=DataType.BITS)], [0x007b, 0x0000], 1),
        ([SimData(15, values=123, datatype=DataType.BITS)], [0x8000, 0x003d, 0x0000], 0),
    ])
    def test_simdevice_build_bits(self, block, registers, addr):
        """Test build_device() ok."""
        sim123 = [SimData(addr, values=123, datatype=DataType.INT16)]
        sd = SimDevice(id=1, simdata=(block, block, sim123, sim123))
        reg_len = len(registers) - 2
        result = {
            "c": (addr, registers, [DataType.BITS] + [0] * reg_len + [DataType.INVALID]),
            "d": (addr, registers, [DataType.BITS] + [0] * reg_len + [DataType.INVALID]),
            "h": (addr, [123, 0], [DataType.INT16, DataType.INVALID]),
            "i": (addr, [123, 0], [DataType.INT16, DataType.INVALID])
        }
        lists = cast(dict[str, SimRegs], sd.build_device())
        assert lists == result

    @pytest.mark.parametrize("count", range(1,4))
    @pytest.mark.parametrize("data_count", range(1,4))
    def test_simdevice_build_count(self, count, data_count):
        """Test build_device() ok."""
        list_data = []
        start_addr = 1
        regs = [123]
        flags = [DataType.REGISTERS]
        for _ in range(data_count):
            list_data.append(SimData(start_addr, count=count, values=123, datatype=DataType.REGISTERS))
            start_addr += count
        sd = SimDevice(id=1, simdata=list_data)
        lists = sd.build_device()
        result = (1, regs*count*data_count + [0], flags*count*data_count + [DataType.INVALID])
        assert lists == result
