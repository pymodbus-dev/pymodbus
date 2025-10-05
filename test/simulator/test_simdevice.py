"""Test SimDevice."""

import pytest

from pymodbus.simulator import SimData, SimDevice


class TestSimDevice:
    """Test simulator device config."""

    simdata1 = SimData(0, values=15)
    simdata2 = SimData(1, values=16)
    simdatadef = SimData(0, values=17, count=10, default=True)

    @pytest.mark.parametrize("kwargs", [
        {"id": 0, "type_check": True, "block_shared": [simdata1]},
        {"id": 0, "block_coil": [simdata1], "block_direct": [simdata1],"block_holding": [simdata1],"block_input": [simdata1],},
        {"id": 0, "block_shared": [simdata1]},
    ])
    def test_simdevice_instanciate(self, kwargs):
        """Test that simdata can be objects."""
        SimDevice(**kwargs)

    @pytest.mark.parametrize("kwargs", [
        {"block_shared": [simdata1]},
        {"id": 0},
        {"id": "not ok", "block_shared": [simdata1]},
        {"id": 1.0, "block_shared": [simdata1]},
        {"id": 256, "block_shared": [simdata1]},
        {"id": -1, "block_shared": [simdata1]},
        {"id": 1, "block_shared": []},
        {"id": 0, "block_shared": [simdata1], "block_coil": [simdata1]},
        {"id": 0, "block_direct": [simdata1],"block_holding": [simdata1], "block_input": [simdata1]},
        {"id": 0, "block_coil": [simdata1], "block_holding": [simdata1], "block_input": [simdata1]},
        {"id": 0, "block_coil": [simdata1], "block_direct": [simdata1], "block_input": [simdata1]},
        {"id": 0, "block_coil": [simdata1], "block_direct": [simdata1], "block_holding": [simdata1]},
    ])
    def test_simdevice_not_ok(self, kwargs):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(**kwargs)

    def test_wrong_block(self):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(id=1, block_shared=SimData(0))
        with pytest.raises(TypeError):
            SimDevice(id=1, block_shared=["no valid"])

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
            a = SimDevice(id=0, block_shared=block)
            assert a.block_shared[0].values == [0]
            assert a.block_shared[0].default
            assert not a.block_shared[1].default
        elif expect == 1:
            a = SimDevice(id=0, block_shared=block)
            assert a.block_shared[0].values == [17]
            assert a.block_shared[0].default
            if len(a.block_shared) > 1:
                assert not a.block_shared[1].default
        else: # expect == 2:
            with pytest.raises(TypeError):
                SimDevice(id=0, block_shared=block)


# test BITS shared/non-shared !
