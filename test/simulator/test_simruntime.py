"""Test SimCore."""
from typing import cast

import pytest

from pymodbus.pdu import ExceptionResponse
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
            return ExceptionResponse(function_code, 1)
        # function_code == 5:
        return None

    @pytest.mark.parametrize(("block", "expect"), [
        ((3, [1], [0xffff]), (3, 16, [1]*16, [1]*16)),
        ((3, [1], [0x0000]), (3, 16, [1]*16, [0]*16)),
        ((3, [1], [0xffff, 0xffff]), (3, 32, [1]*32, [1]*32)),
    ])
    async def test_simruntime_convert_bit(self, block, expect):
        """Test that simdata can be objects."""
        result = SimRuntime.convert_to_bit(block)
        assert result == expect

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
            assert isinstance(ret, ExceptionResponse)
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
            assert isinstance(ret, ExceptionResponse)
        else:
            assert len(cast(list[int], ret)) == expect
