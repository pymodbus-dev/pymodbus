"""Test SimCore."""

import pytest

from pymodbus.constants import ExcCodes
from pymodbus.simulator import DataType, SimData, SimDevice
from pymodbus.simulator.simruntime import SimRuntime


class TestSimRuntime:
    """Test simulator runtime component."""

    async def my_action(
            self,
            function_code,
            _start_address,
            _address,
            _count,
            current_registers,
            set_values
         ):
        """Run action."""
        if function_code in {1, 2, 3}:
            current_registers[1] = 17
        if function_code == 4:
            return ExcCodes.ILLEGAL_ADDRESS
        elif function_code == 15:
            set_values[0] = False
        elif function_code == 16:
            set_values[0] = 17
    sd_block = (
        [SimData(0, values=[14, 15, 16], datatype=DataType.BITS)],
        [SimData(0, values=[14, 15, 16], datatype=DataType.BITS)],
        [SimData(0, values=[14, 15, 16], datatype=DataType.REGISTERS)],
        [SimData(0, values=[14, 15, 16], datatype=DataType.REGISTERS)],
    )
    sd_shared = SimData(0, datatype=DataType.REGISTERS, values=[14, 15, 16])
    block_ids = {
        1: "c",
        2: "d",
        3: "h",
        4: "i",
        15: "c",
        16: "h"
        }

    def test_simruntime_instanciate(self):
        """Test that simdata can be objects."""
        SimRuntime(SimDevice(0, self.sd_block))
        SimRuntime(SimDevice(0, self.sd_shared))

    @pytest.mark.parametrize("block", [False, True])
    @pytest.mark.parametrize("fc", range(1, 25))
    async def test_simruntime_fc(self, fc, block):
        """Test that simdata can be objects."""
        sd = SimDevice(1, simdata=(self.sd_block if block else self.sd_shared))
        rt = SimRuntime(sd)
        if fc in (1,2,3,4,5,6,15,16,22,23):
            ret = await rt.get_block(fc, 1, 1, None)
            assert not isinstance(ret, ExcCodes)
        else:
            with pytest.raises(RuntimeError):
                await rt.get_block(fc, 1, 1, None)

    @pytest.mark.parametrize("block", [True, False])
    @pytest.mark.parametrize(("fc", "values", "expect"), [
        (1, None, [14, 17, 16, 0]),
        (2, None, [14, 17, 16, 0]),
        (3, None, [14, 17, 16, 0]),
        (4, None, -1),
        (15, [True, False], [12, 15, 16, 0]),
        (16, [12], [17, 15, 16, 0]),
        ])
    async def test_simruntime_action(self, block, fc, values, expect):
        """Test that simdata can be objects."""
        rt = SimRuntime(SimDevice(1,
            action=self.my_action,
            simdata=(self.sd_block if block else self.sd_shared))
        )
        block_id = self.block_ids[fc] if block else "x"
        count = len(values) if values else 2
        ret = await rt.get_block(fc, 0, count, values)
        if expect == -1:
            assert ret == ExcCodes.ILLEGAL_ADDRESS
        else:
            assert rt.block[block_id][2] == expect

    @pytest.mark.parametrize("block", [True, False])
    @pytest.mark.parametrize(("fc", "addr", "values", "expect"), [
        (1, 0, None, [False, True]),
        (2, 0, None, [False, True]),
        (3, 0, None, [14, 15]),
        (4, 0, None, [14, 15]),
        (15, 0, [True, False], [True, False]),
        (16, 0, [12], [12]),
        ])
    async def test_simruntime_block(self, block, fc, addr, values, expect):
        """Test that simdata can be objects."""
        rt = SimRuntime(SimDevice(1,
            simdata=(self.sd_block if block else self.sd_shared))
        )
        count = len(values) if values else 2
        ret = await rt.get_block(fc, addr, count, values)
        assert ret == expect

    async def test_simruntime_getValues(self):
        """Test that simdata can be objects."""
        sd = SimDevice(0, simdata=SimData(10, values=15, datatype=DataType.REGISTERS))
        rt = SimRuntime(sd)
        result = await rt.async_getValues(0x03, 10, 1)
        assert result == [15]
        result = await rt.async_getValues(0x03, 15, 1)
        assert isinstance(result, ExcCodes)

    async def test_simruntime_setValues(self):
        """Test that simdata can be objects."""
        sd = SimDevice(0, simdata=SimData(10, values=15, datatype=DataType.REGISTERS))
        rt = SimRuntime(sd)
        result = await rt.async_setValues(0x03, 10, [1])
        assert not result
        result2 = await rt.async_getValues(0x03, 10, 1)
        assert result2 == [1]
        result3 = await rt.async_setValues(0x03, 15, [1])
        assert isinstance(result3, ExcCodes)
