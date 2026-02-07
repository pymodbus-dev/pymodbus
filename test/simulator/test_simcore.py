"""Test SimCore."""
import pytest

from pymodbus.constants import DataType
from pymodbus.simulator import SimData, SimDevice
from pymodbus.simulator.simcore import SimCore


class TestSimCore:
    """Test simulator core component."""

    simdata1 = SimData(0, datatype=DataType.INT16, values=15)
    simdata2 = SimData(1, datatype=DataType.INT16, values=16)
    simdata3 = SimData(1, datatype=DataType.BITS, values=16)

    @pytest.mark.parametrize("devices", [
        SimDevice(0, simdata=simdata3),
        [SimDevice(0, simdata=simdata3)],
        [SimDevice(0, simdata=simdata3), SimDevice(1, simdata=simdata3)],
        SimDevice(0, simdata=([simdata3], [simdata3], [simdata1], [simdata3])),
    ])
    def test_simcore_instanciate(self, devices):
        """Test that l can be objects."""
        SimCore(devices=devices)

    @pytest.mark.parametrize("devices", [
        "not ok",
        ["not ok"],
        [SimDevice(1, simdata=simdata3), SimDevice(1, simdata=simdata3)],
    ])
    def test_simdcore_not_ok(self, devices):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimCore(devices=devices)

    @pytest.mark.parametrize("kwargs", [
        {"device_id": 4, "func_code": 3, "address": 0, "count": 1},
    ])
    async def test_simdcore_get(self, kwargs):
        """Test that simdata can be objects."""
        core = SimCore(devices=SimDevice(0, simdata=self.simdata2))
        await core.async_getValues(**kwargs)

    @pytest.mark.parametrize("kwargs", [
        {"device_id": 4, "func_code": 3, "address": 0, "values": [1]},
    ])
    async def test_simdcore_set(self, kwargs):
        """Test that simdata can be objects."""
        core = SimCore(devices=SimDevice(0, simdata=self.simdata2))
        await core.async_setValues(**kwargs)
