"""Test pdu."""

import pytest

from pymodbus.simulator import SimData, SimDataType, SimDevice


class TestSimData:
    """Test simulator data config."""

    def test_instanciate(self):
        """Test that simdata can be objects."""
        a = SimData(0)
        SimDevice(0, block_shared=[a])

    @pytest.mark.parametrize("address", ["not ok", 1.0, -1, 70000])
    def test_simdata_address(self, address):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimData(address)
        SimData(0)

    @pytest.mark.parametrize("count", ["not ok", 1.0, -1, 70000])
    def test_simdata_count(self, count):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimData(address=0, count=count)
        SimData(0, count=2)

    @pytest.mark.parametrize("datatype", ["not ok", 1.0, 11])
    def test_simdata_datatype(self, datatype):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimData(0, datatype=datatype)
        SimData(0, datatype=SimDataType.BITS)

    @pytest.mark.parametrize("action", ["my action"])
    def test_simdata_action(self, action):
        """Test that simdata can be objects."""
        def dummy_action():
            """Set action."""

        with pytest.raises(TypeError):
            SimData(0, action=action)
        SimData(0, action=dummy_action)

