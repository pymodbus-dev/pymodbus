"""Test SimDevice."""

import pytest

from pymodbus.simulator import SimData, SimDevice


class TestSimDevice:
    """Test simulator device config."""

    simdata1 = SimData(0, values=15)
    simdata2 = SimData(1, values=16)
    simdatadef = SimData(0, values=17, count=10, default=True)

    @pytest.mark.parametrize("kwargs", [
        {"id": 0, "type_check": True, "registers": [simdata1]},
        {"id": 0, "registers": [simdatadef], "offset_address": (1, 4, 6, 8)},
    ])
    def test_simdevice_instanciate(self, kwargs):
        """Test that simdata can be objects."""
        SimDevice(**kwargs)

    @pytest.mark.parametrize("kwargs", [
        {"registers": [simdata1]},
        {"id": 0},
        {"id": "not ok", "registers": [simdata1]},
        {"id": 1.0, "registers": [simdata1]},
        {"id": 256, "registers": [simdata1]},
        {"id": -1, "registers": [simdata1]},
        {"id": 1, "registers": []},
        {"id": 0, "registers": [SimData(1, 10, default=True), SimData(200)]},
        {"id": 0, "registers": [SimData(10, 10, default=True), SimData(2)]},
        {"id": 0, "registers": [SimData(1, 2), SimData(2)]},
        {"id": 0, "registers": [simdatadef, SimData(2, 10, default=True)]},
        {"id": 0, "registers": [simdata1], "type_check": "jan"},
        {"id": 0, "registers": [simdatadef], "offset_address": ()},
        {"id": 0, "registers": [simdatadef], "offset_address": (1, 2, 3)},
        {"id": 0, "registers": [simdatadef], "offset_address": (1, 3, 2, 4)},
        {"id": 0, "registers": [simdatadef], "offset_address": (1, 3, 2, 20)},
        {"id": 0, "registers": [SimData(1, 10, default=True)], "offset_address": (1, 3, 2, 15)},
        {"id": 0, "registers": [SimData(10, 10, default=True)], "offset_address": (1, 3, 2, 4)},
    ])
    def test_simdevice_not_ok(self, kwargs):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(**kwargs)

    def test_wrong_block(self):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(id=1, registers=SimData(0))
        with pytest.raises(TypeError):
            SimDevice(id=1, registers=["no valid"])

    @pytest.mark.parametrize(("block", "expect"), [
        ([simdata1], 0),
        ([simdatadef], 1),
        ([simdatadef, simdata1], 1),
        ([simdata1, simdatadef], 1),
        ([simdata1, simdata2, simdatadef], 1),
    ])
    def test_simdevice_block(self, block, expect):
        """Test that simdata can be objects."""
        if not expect:
            a = SimDevice(id=0, registers=block)
            assert a.registers[0].values == [0]
            assert a.registers[0].default
            assert not a.registers[1].default
        elif expect == 1:
            a = SimDevice(id=0, registers=block)
            assert a.registers[0].values == [17]
            assert a.registers[0].default
            if len(a.registers) > 1:
                assert not a.registers[1].default
        else: # expect == 2:
            with pytest.raises(TypeError):
                SimDevice(id=0, registers=block)


# test BITS shared/non-shared !
