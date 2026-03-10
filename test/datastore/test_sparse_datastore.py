"""Test framers."""

import pytest

from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.exceptions import ParameterException


class TestSparseDataStore:
    """Unittest for the pymodbus.datastore.remote module."""

    data_in_block: dict[int, int | list[int]] = {
        1: 6720,
        2: 130,
        30: [0x0D, 0xFE],
        105: [1, 2, 3, 4],
        20000: [45, 241, 48],
        20008: 38,
        48140: [0x4208, 0xCCCD],
    }

    def test_sparse_datastore(self):
        """Test check frame."""
        ModbusSparseDataBlock(self.data_in_block)
        ModbusSparseDataBlock([1, 2, 3])
        ModbusSparseDataBlock()
        with pytest.raises(ParameterException):
            ModbusSparseDataBlock(1)
