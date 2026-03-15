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
            _address,
            current_registers,
            _new_registers
        ):
        """Run action."""
        if function_code == 3:
            return current_registers
        if function_code == 4:
            return ExcCodes.ILLEGAL_ADDRESS
        # function_code == 5:
        return None

    @pytest.mark.parametrize("kwargs", [
        {"id": 0, "simdata": ([SimData(0, datatype=DataType.BITS, values=15)],
                              [SimData(0, datatype=DataType.BITS, values=15)],
                              [SimData(0, datatype=DataType.INT16, values=15)],
                              [SimData(0, datatype=DataType.INT16, values=15)])},
        {"id": 0, "simdata": SimData(0, datatype=DataType.INT16, values=15)},
    ])
    def test_simruntime_instanciate(self, kwargs):
        """Test that simdata can be objects."""
        sd = SimDevice(**kwargs)
        SimRuntime(sd)

    @pytest.mark.parametrize(("args", "expect"), [
        ((3, 1, 1, None), -1),
        ((3, 200, 1, None), -1),
        ((3, 15, 200, None), -1),
        ((3, 15, 2, None), 2),
        ((3, 19, 1, [1, 2 , 3]), -1),
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
        ((3, 11, 1, [1, 2, 3]), [0, 1, 2, 3, 0, 0]),
        ((3, 12, 1, [1, 2 , 3]), [0, 0, 1, 2, 3, 0]),
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

    @pytest.mark.parametrize(("args", "expect"), [
        ((3, 15, 2, None), 2),
        ((4, 15, 2, None), -1),
        ((5, 15, 2, None), 2),
    ])
    async def test_simruntime_action(self, args, expect):
        """Test that simdata can be objects."""
        sd = SimDevice(0, action=self.my_action, simdata=[
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
