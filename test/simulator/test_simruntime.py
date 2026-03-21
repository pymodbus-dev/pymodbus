"""Test SimCore."""
from typing import cast

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
        [SimData(0, count=2, values=15, datatype=DataType.BITS)],
        [SimData(0, count=2, values=15, datatype=DataType.BITS)],
        [SimData(0, count=2, values=15, datatype=DataType.REGISTERS)],
        [SimData(0, count=2, values=15, datatype=DataType.REGISTERS)],
    )
    sd_shared = SimData(0, count=2, datatype=DataType.REGISTERS, values=15)

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

    @pytest.mark.parametrize(("block", "fc", "values", "expect"), [
        (False, 1, None, [15, 17, 0]),
        (True, 1, None, [15, 17, 0]),
        (False, 2, None, [15, 17, 0]),
        (True, 2, None, [15, 17, 0]),
        (False, 3, None, [15, 17, 0]),
        (True, 3, None, [15, 17, 0]),
        (False, 4, None, -1),
        (True, 4, None, -1),
        (False, 15, [True, False], [15, 9, 0]),
        (True, 15, [True, False], [9, 15, 0]),
        (False, 16, [12], [15, 17, 0]),
        (True, 16, [12], [15, 17, 0]),
        ])
    async def test_simruntime_action(self, block, fc, values, expect):
        """Test that simdata can be objects."""
        rt = SimRuntime(SimDevice(1,
            action=self.my_action,
            simdata=(self.sd_block if block else self.sd_shared))
        )
        if block:
            block_id = {
                1: "c",
                2: "d",
                3: "h",
                4: "i",
                15: "c",
                16: "h"
                }[fc]
        else:
            block_id = "x"
        count = len(values) if values else 2
        ret = await rt.get_block(fc, 1, count, values)
        if expect == -1:
            assert ret == ExcCodes.ILLEGAL_ADDRESS
        else:
            assert rt.block[block_id][2] == expect
   
    @pytest.mark.parametrize(("args", "expect"), [
        ((3, 1, 1, None), 1),
        ((3, 200, 1, None), -1),
        ((3, 15, 200, None), -1),
        ((3, 15, 2, None), 2),
        # ((3, 19, 1, [1, 2 , 3]), -1),
        ((3, 19, 1, [1]), 1),
        ((3, 10, 2, None), -1),
        ((3, 10, 1, [1]), -1),
    ])
    async def test_simruntime_block(self, args, expect):
        """Test that simdata can be objects."""
        sd = SimDevice(0, simdata=[
            SimData(10, count=1, values=0, datatype=DataType.REGISTERS, readonly=True),
            SimData(11, count=1, values=0, datatype=DataType.INVALID),
            SimData(12, count=8, values=0, datatype=DataType.REGISTERS),
        ])
        rt = SimRuntime(sd)
        ret = await rt.get_block(*args)
        if expect == -1:
            assert isinstance(ret, ExcCodes)
        else:
            assert len(cast(list[int], ret)) == expect


    @pytest.mark.parametrize(("args", "expect"), [
        ((3, 10, 1, [1]), [1, 0, 0, 0, 0, 0]),
        # ((3, 11, 1, [1, 2, 3]), [0, 1, 2, 3, 0, 0]),
        # ((3, 12, 1, [1, 2 , 3]), [0, 0, 1, 2, 3, 0]),
    ])
    async def test_simruntime_block_set(self, args, expect):
        """Test that simdata can be objects."""
        sd = SimDevice(0, simdata=
                       SimData(10, count=5, values=0, datatype=DataType.REGISTERS)
                    )
        rt = SimRuntime(sd)

        ret = await rt.get_block(*args)
        assert ret == args[3]
        assert rt.block["x"][2] == expect


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
