"""Test SimCore."""


from pymodbus.simulator import SimCore, SimData, SimDevice


class TestSimCore:
    """Test simulator data config."""

    def test_instanciate(self):
        """Test that simdata can be objects."""
        SimCore()

    def test_build_block(self):
        """Test that simdata can be objects."""
        SimCore.build_block(None)

    def test_build_config(self):
        """Test that simdata can be objects."""
        device = SimDevice(17, registers=[SimData(0)])
        SimCore.build_block([device])
