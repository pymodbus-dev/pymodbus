"""Test SimData."""
import pytest

from pymodbus.constants import DataType
from pymodbus.simulator import SimData


class TestSimData:
    """Test simulator data config."""

    async def async_dummy_action(self):
        """Set action."""

    def dummy_action(self):
        """Set action."""

    @pytest.mark.parametrize("kwargs", [
        {"address": 0},
        {"address": 65535},
        {"address": 65535, "count": 1},
        {"address": 0, "count": 65536},
        {"address": 1, "count": 65535},
        {"address": 1, "count": 10, "invalid": True},
        {"address": 3, "count": 10, "readonly": True},
        {"address": 4, "datatype": DataType.INT16, "values": 17},
        {"address": 5, "datatype": DataType.INT16, "values": [17, 18]},
        {"address": 6, "count": 10, "datatype": DataType.INT16, "values": [17, 18]},
        {"address": 7, "datatype": DataType.STRING, "values": "test"},
        {"address": 8, "count": 10, "datatype": DataType.STRING, "values": "test"},
        {"address": 9, "action": async_dummy_action},
        {"address": 0, "datatype": DataType.REGISTERS, "values": 17, "count": 5},
        {"address": 1, "datatype": DataType.INT16, "values": 17, "invalid": True},
        {"address": 3, "datatype": DataType.INT16, "values": 17, "readonly": True},
        {"address": 0, "count": 2^16 -1},
        {"address": 4, "datatype": DataType.BITS},
        {"address": 4, "datatype": DataType.BITS, "values": 117},
        {"address": 1, "datatype": DataType.BITS, "values": True},
        {"address": 4, "datatype": DataType.BITS, "values": [True, True]},
        {"address": 2, "values": 17},
    ])
    def test_simdata_instanciate(self, kwargs):
        """Test that simdata can be objects."""
        SimData(**kwargs)

    @pytest.mark.parametrize("kwargs", [
        {"address": "not ok"},
        {"address": 1.0},
        {"address": -1},
        {"address": 70000},
        {"address": 1, "count": 65536},
        {"address": 65535, "count": 2},
        {"address": 1, "count": "not ok"},
        {"address": 1, "count": 1.0},
        {"address": 1, "count": -1},
        {"address": 1, "count": 70000},
        {"address": 1, "count": 0},
        {"address": 1, "datatype": "not ok"},
        {"address": 1, "datatype": 11},
        {"address": 1, "action": "not ok"},
        {"address": 1, "action": dummy_action},
    ])
    def test_simdata_not_ok(self, kwargs):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimData(**kwargs)

    @pytest.mark.parametrize(("value", "value_type"), [
        ("ok str", DataType.STRING),
        (1.0, DataType.FLOAT32),
        ([1.0, 2.0], DataType.FLOAT32),
        (1, DataType.INT32),
        ([1, 2], DataType.INT32),
        (11, DataType.REGISTERS),
        ([11, 12], DataType.REGISTERS),
        (True, DataType.BITS),
        ([True, False], DataType.BITS),
        ])
    def test_simdata_value_ok(self, value, value_type):
        """Test simdata value."""
        SimData(0, values=value, datatype=value_type)

    @pytest.mark.parametrize(("value", "value_type"), [
        (["ok str", "ok2"], DataType.STRING),
        (1, DataType.STRING),
        (1, DataType.FLOAT32),
        ([1.0, 2], DataType.FLOAT32),
        (1.0, DataType.INT32),
        ([1, 2.0], DataType.INT32),
        ("not ok", DataType.REGISTERS),
        (1.0, DataType.REGISTERS),
        ([11, 12.0], DataType.REGISTERS),
        (1.0, DataType.BITS),
        ([True, 1.0], DataType.BITS),
        ])
    def test_simdata_value_not_ok(self, value, value_type):
        """Test simdata value."""
        with pytest.raises(TypeError):
            SimData(0, values=value, datatype=value_type)
