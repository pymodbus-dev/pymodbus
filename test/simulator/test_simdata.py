"""Test SimData."""

import pytest

from pymodbus.constants import DataType
from pymodbus.simulator import SimData


class TestSimData:
    """Test simulator data config."""

    def test_instanciate(self):
        """Test that simdata can be objects."""
        SimData(0)

    @pytest.mark.parametrize("address", ["not ok", 1.0, -1, 70000])
    def test_simdata_address(self, address):
        """Test simdata address."""
        with pytest.raises(TypeError):
            SimData(address)
        SimData(0)

    @pytest.mark.parametrize("count", ["not ok", 1.0, -1, 70000])
    def test_simdata_count(self, count):
        """Test simdata count."""
        with pytest.raises(TypeError):
            SimData(address=0, count=count)
        SimData(0, count=2)

    @pytest.mark.parametrize("datatype", ["not ok", 1.0, 11])
    def test_simdata_datatype(self, datatype):
        """Test simdata datatype."""
        with pytest.raises(TypeError):
            SimData(0, datatype=datatype)
        SimData(0, datatype=DataType.BITS)

    @pytest.mark.parametrize(("value", "value_type"), [
        ("ok str", DataType.STRING),
        (1.0, DataType.FLOAT32),
        (11, DataType.REGISTERS),
        (True, DataType.BITS),
        # (17, DataType.DEFAULT),
        ])
    def test_simdata_value_ok(self, value, value_type):
        """Test simdata value."""
        SimData(0, value=value, datatype=value_type)

    @pytest.mark.parametrize(("value", "value_type"), [
        ([True, False], DataType.BITS),
        ({0: 1}, DataType.REGISTERS),
        ((1, 0), DataType.REGISTERS),
        (123, DataType.STRING),
        ("", DataType.INT16),
        (123, DataType.FLOAT32),
        (123.0, DataType.BITS),
        (123.0, DataType.REGISTERS),
        # ("", DataType.DEFAULT),
        ])
    def test_simdata_value_not_ok(self, value, value_type):
        """Test simdata value."""
        with pytest.raises(TypeError):
            SimData(0, value=value, datatype=value_type)

    def test_simdata_action(self):
        """Test simdata action."""
        def dummy_action():
            """Set action."""

        async def async_dummy_action():
            """Set action."""

        with pytest.raises(TypeError):
            SimData(0, action="not_ok")
        SimData(0, action=dummy_action)
        SimData(0, action=async_dummy_action)
        # with pytest.raises(TypeError):
        #     SimData(0, datatype=DataType.DEFAULT, action=dummy_action)
