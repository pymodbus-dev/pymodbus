"""Test SimData."""
import pytest

from pymodbus.simulator.simutils import SimUtils


class TestSimUtils:
    """Test simulator utilities."""

    def test_simutils_instanciate(self):
        """Test that simdata cannot be a objects."""
        with pytest.raises(RuntimeError):
            SimUtils()

    @pytest.mark.parametrize(("bits", "registers"), [
        ([True] + [False] * 8 + [True] + [False]*6, [513]),
        ([True] + [False] * 8 + [True] + [False]*6 + [False] + [True] + [False] * 6 + [True] + [False]*7, [513, 258]),
    ])
    def test_simutils_bitsToRegisters(self, bits, registers):
        """Test convert list[bool] to list[int]."""
        assert registers == SimUtils.bitsToRegisters(bits)

    @pytest.mark.parametrize(("bits"), [
        ([True] + [False] * 8 + [True] + [False]*5),
        ([True] + [False] * 8 + [True] + [False]*6 + [False] + [True] + [False] * 6 + [True] + [False]*6),
    ])
    def test_simutils_bitsToRegisters_not_ok(self, bits):
        """Test convert list[bool] to list[int]."""
        with pytest.raises(TypeError):
            SimUtils.bitsToRegisters(bits)

    @pytest.mark.parametrize(("bits", "registers"), [
        ([True] + [False] * 8 + [True] + [False]*6, [513]),
        ([True] + [False] * 8 + [True] + [False]*6 + [False] + [True] + [False] * 6 + [True] + [False]*7, [513, 258]),
    ])
    def test_simutils_registersToBits(self, bits, registers):
        """Test convert list[bool] to list[int]."""
        new_bits = SimUtils.registersToBits(registers)
        assert bits == new_bits


    @pytest.mark.parametrize(("registers", "offset", "bits", "expect"), [
        ([513], 0, [], [513]),
        ([513], 0, [False], [512]),
        ([513], 1, [False], [513]),
        ([513], 0, [True, True], [515]),
        ([513], 1, [True], [515]),
        ([513], 15, [True], [33281]),
        ([513, 0], 15, [True, True], [33281, 1]),
        ([513, 0], 15, [True, False], [33281, 0]),
    ])
    def test_simutils_mergeBitsToRegisters(self, registers, offset, bits, expect):
        """Test convert list[bool] to list[int]."""
        temp_regs = registers.copy()
        SimUtils.mergeBitsToRegisters(offset, temp_regs, bits)
        assert temp_regs == expect


    @pytest.mark.parametrize(("byte_list", "expect"), [
        (b'\x01\x01', [257]),
        (b'\x01\x02', [258]),
        (b'\x01\x01\x01\x02', [257, 258]),
    ])
    def test_simutils_bytesToRegisters(self, byte_list, expect):
        """Test convert list[bool] to list[int]."""
        regs = SimUtils.bytesToRegisters(byte_list)
        assert regs == expect
