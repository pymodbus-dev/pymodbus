"""Test SimDevice."""

import pytest

from pymodbus.simulator import SimData, SimDevice


class TestSimDevice:
    """Test simulator device config."""

    def test_instanciate(self):
        """Test that simdata can be objects."""
        a = SimData(0)
        SimDevice(0, block_shared=[a])

    @pytest.mark.parametrize("id", ["not ok", 1.0, 256])
    def test_simid(self, id):
        """Test device id."""
        with pytest.raises(TypeError):
            SimDevice(id=id)
        SimDevice(id=1, block_shared=[SimData(0)])

    def test_block_shared(self):
        """Test shared block."""
        with pytest.raises(TypeError):
            SimDevice(id=1, block_shared=[SimData(0)], block_coil=[SimData(0)])
        SimDevice(id=1, block_shared=[SimData(0)])

    def test_block_non_shared(self):
        """Test non-shared block."""
        with pytest.raises(TypeError):
            SimDevice(id=1, block_coil=[SimData(0)])
        SimDevice(id=1,
            block_coil=[SimData(0)],
            block_direct=[SimData(0)],
            block_holding=[SimData(0)],
            block_input=[SimData(0)],
        )

    def test_wrong_block(self):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(id=1, block_shared=SimData(0))
        with pytest.raises(TypeError):
            SimDevice(id=1, block_coil=["no valid"])
