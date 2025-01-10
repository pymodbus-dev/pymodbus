"""Test pdu."""

import pytest

from pymodbus.simulator import SimData, SimDataType, SimDevice


class TestSimData:
    """Test simulator data config."""

    def test_instanciate(self):
        """Test that simdata can be objects."""
        a = SimData(0)
        SimDevice(0, block_shared=[a])

    @pytest.mark.parametrize("start_register", ["not ok", 1.0, -1, 70000])
    def test_simdata_start_register(self, start_register):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimData(start_register=start_register)
        SimData(0)

    @pytest.mark.parametrize("count", ["not ok", 1.0, -1, 70000])
    def test_simdata_count(self, count):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimData(start_register=0, count=count)
        SimData(start_register=0, count=2)

    @pytest.mark.parametrize("datatype", ["not ok", 1.0, 11])
    def test_simdata_datatype(self, datatype):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimData(start_register=0, datatype=datatype)
        SimData(start_register=0, datatype=SimDataType.BITS)

    @pytest.mark.parametrize("action", ["my action"])
    def test_simdata_action(self, action):
        """Test that simdata can be objects."""
        def dummy_action():
            """Set action."""

        with pytest.raises(TypeError):
            SimData(start_register=0, action=action)
        SimData(start_register=0, action=dummy_action)

    @pytest.mark.parametrize("id", ["not ok", 1.0, 256])
    def test_simid(self, id):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(id=id)
        SimDevice(id=1, block_shared=[SimData(0)])

    def test_block_shared(self):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(id=1, block_shared=[SimData(0)], block_coil=[SimData(0)])
        with pytest.raises(TypeError):
            SimDevice(id=1, block_coil=[SimData(0)])

    def test_wrong_block(self):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(id=1, block_shared=SimData(0))
        with pytest.raises(TypeError):
            SimDevice(id=1, block_coil=["no valid"])
