"""Test SimRuntime."""

import pytest

from pymodbus.simulator import SimData, SimDevice, SimDevices
from pymodbus.simulator.simruntime import SimRuntimeRegister, SimSetupRuntime


class TestSimRuntime:
    """Test simulator runtime generator."""

    TOTAL_FLAGS = (
        SimRuntimeRegister.FLAG_ACTION |
        SimRuntimeRegister.FLAG_INVALID |
        SimRuntimeRegister.FLAG_NO_DIRECT |
        SimRuntimeRegister.FLAG_READONLY
    )

    @pytest.mark.parametrize("onoff", [True, False])
    @pytest.mark.parametrize(("reg_flag", "exp_size"), [
        (SimRuntimeRegister.FLAG_REG_SIZE_1, 1),
        (SimRuntimeRegister.FLAG_REG_SIZE_2, 2),
        (SimRuntimeRegister.FLAG_REG_SIZE_4, 4),
    ])
    @pytest.mark.parametrize(("test_flag", "exp_flags"), [
        (SimRuntimeRegister.FLAG_ACTION, [False, True, True, True]),
        (SimRuntimeRegister.FLAG_INVALID, [True, False, True, True]),
        (SimRuntimeRegister.FLAG_NO_DIRECT, [True, True, False, True]),
        (SimRuntimeRegister.FLAG_READONLY, [True, True, True, False]),
    ])
    def test_simruntimeregister_instanciate(self, onoff, reg_flag, exp_size, test_flag, exp_flags):
        """Test that SimRuntimeRegister can be objects."""
        flags = reg_flag
        res_flags = exp_flags.copy()
        if onoff:
            flags += test_flag
            for i in range(4):
                res_flags[i] = not res_flags[i]
        else:
            flags += self.TOTAL_FLAGS^test_flag
        reg = SimRuntimeRegister(flags, 15)
        assert reg.data_size() == exp_size
        assert reg.is_action() == res_flags[0]
        assert reg.is_invalid() == res_flags[1]
        assert reg.is_no_direct() == res_flags[2]
        assert reg.is_readonly() == res_flags[3]

    def test_simsetupruntime(self):
        """Test simSetupRuntime."""
        SimSetupRuntime()

    @pytest.mark.parametrize(("devices", "expect"), [
        ("not ok", 1),
        (SimDevices([SimDevice(0, [SimData(0)])]), 0),
    ])
    def test_simsetupruntime_build(self, devices, expect):
        """Test simSetupRuntime."""
        a = SimSetupRuntime()
        if expect:
            with pytest.raises(TypeError):
                a.build_runtime(devices)
        else:
            a.build_runtime(devices)
