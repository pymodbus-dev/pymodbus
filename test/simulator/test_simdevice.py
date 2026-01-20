"""Test SimDevice."""


import pytest

from pymodbus.constants import DataType
from pymodbus.simulator import SimData, SimDevice, SimDevices


class TestSimDevice:
    """Test simulator device config."""

    simdata1 = SimData(0, values=15)
    simdata2 = SimData(1, values=16)
    simdatadef = SimData(0, values=17, count=10)

    @pytest.mark.parametrize("kwargs", [
        {"id": 0, "registers": [simdata1], "default": simdatadef},
        {"id": 0, "registers": [], "default": simdatadef},
        {"id": 0, "type_check": True, "registers": [simdata1]},
        {"id": 0, "registers": [], "default": simdatadef, "offset_address": (1, 4, 6, 8)},
        {"id": 0, "registers": [simdata1], "endian": (False, True)},
        {"id": 0, "registers": [simdata1], "endian": (True, False)},
        {"id": 0, "registers": [simdata1], "identity": "my server"},
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
        {"id": 1, "registers": [simdata1], "word_order_big": "hmm"},
        {"id": 1, "registers": [simdata1], "byte_order_big": "hmm"},
        {"id": 0, "registers": [SimData(200)], "default": SimData(1, 10)},
        {"id": 0, "registers": [SimData(2)], "default": SimData(10, 10)},
        {"id": 0, "registers": [SimData(1, 2), SimData(2)]},
        {"id": 0, "registers": [simdatadef, SimData(2, 10)]},
        {"id": 0, "registers": [simdata1], "type_check": "hmm"},
        {"id": 0, "registers": [simdatadef], "offset_address": 117},
        {"id": 0, "registers": [simdatadef], "offset_address": (1, 2, 3)},
        {"id": 0, "registers": [simdatadef], "offset_address": (1, 3, 2, 4)},
        {"id": 0, "registers": [simdatadef], "offset_address": (1, 3, 2, 20)},
        {"id": 0, "registers": [SimData(1, 10)], "offset_address": (1, 3, 2, 15)},
        {"id": 0, "registers": [SimData(10, 10)], "offset_address": (1, 3, 2, 4)},
        {"id": 0, "registers": [simdatadef], "offset_address": ()},
        {"id": 0, "registers": [simdata1], "identity": 123},
        {"id": 0, "registers": [simdata1], "identity": None},
    ])
    def test_simdevice_not_ok(self, kwargs):
        """Test that simdata can be objects."""
        with pytest.raises(TypeError):
            SimDevice(**kwargs)

    @pytest.mark.parametrize(("block", "default", "expect"), [
        ([simdata1], None, 0),
        ([SimData(0, values=0xffff, datatype=DataType.BITS)], None, 0),
        ([SimData(0, values=[0xffff], datatype=DataType.BITS)], None, 0),
        ([SimData(0, values=[True], datatype=DataType.BITS)], None, 0),
        ([SimData(0, values="hello", datatype=DataType.STRING)], None, 0),
        ([], simdatadef, 1),
        ([simdata1], simdatadef, 1),
        ([simdata1, simdata2], simdatadef, 1),
        ([simdata1, simdata1], simdatadef, 2),
        (SimData(0), None, 2),
        ("no valid", None, 2),
        (["no valid"], None, 2),
        ([simdata1], "no valid", 2),
        ([simdata1], [simdata1], 2),
        ([simdata1], SimData(1, 10, datatype=DataType.INT16), 2),
    ])
    def test_simdevice_block(self, block, default, expect):
        """Test that simdata can be objects."""
        if not expect:
            SimDevice(id=0, default=default, registers=block)
        elif expect == 1:
            SimDevice(id=0, default=default, registers=block)
        else: # expect == 2:
            with pytest.raises(TypeError):
                SimDevice(id=0, default=default, registers=block)

    @pytest.mark.parametrize(("offset", "expect"), [
        ("not ok", 1),
        (["not ok"], 1),
        ([1, 2, 3, 4], 1),
        ((1, 2), 1),
        ((4, 2, 3, 5), 1),
        ((1, 4, 3, 5), 1),
        ((1, 2, 3, 11), 1),
        ((1, 2, 3, 4), 0),
    ])
    def test_simdevice_offset(self, offset, expect):
        """Test offset."""
        if expect:
            with pytest.raises(TypeError):
                SimDevice(id=0, default=self.simdatadef, registers=[], offset_address=offset)
        else:
            SimDevice(id=0, default=self.simdatadef, registers=[], offset_address=offset)

    @pytest.mark.parametrize(("endian", "expect"), [
        ("not ok", 1),
        (None, 1),
        (["not ok"], 1),
        (("not ok"), 1),  # noqa: PT014
        (("not ok", "not_ok"), 1),
        ((True, False), 0),
    ])
    def test_simdevice_endian(self, endian, expect):
        """Test offset."""
        if expect:
            with pytest.raises(TypeError):
                SimDevice(id=0, registers=[self.simdata1], endian=endian)
        else:
            SimDevice(id=0, registers=[self.simdata1], endian=endian)

    @pytest.mark.parametrize("block", [
        [SimDevice(1, [simdata1])],
        [SimDevice(0, [simdata1])],
        [SimDevice(0, [simdata1]), SimDevice(1, [simdata1])],
        [SimDevice(2, [simdata1]), SimDevice(3, [simdata1])],
    ])
    def test_simdevices_instanciate(self, block):
        """Test SimDevices."""
        SimDevices(block)

    @pytest.mark.parametrize("block", [
        "not ok",
        ["not ok"],
        [],
        SimDevice(0, [simdata1]),
        [SimDevice(0, [simdata1]), SimDevice(0, [simdata1])],
        [SimDevice(2, [simdata1]), SimDevice(2, [simdata1])],
        [SimDevice(2, [simdata1]), SimDevice(3, [simdata1]), SimDevice(3, [simdata1])],
    ])
    def test_simdevices_not_ok(self, block):
        """Test SimDevices."""
        with pytest.raises(TypeError):
            SimDevices(block)
