"""Test SimCore."""


from pymodbus.simulator import SimCore


class TestSimCore:
    """Test simulator data config."""

    def test_instanciate(self):
        """Test that simdata can be objects."""
        SimCore()
