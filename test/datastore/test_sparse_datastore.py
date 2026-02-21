"""Test framers."""
from unittest import mock

import pytest

from pymodbus.constants import ExcCodes
from pymodbus.datastore import ModbusSparseDataBlock
from pymodbus.exceptions import ParameterException


class TestRemoteDataStore:
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

    async def test_sparse_datastore_async(self):
        """Test check frame."""
        datablock = ModbusSparseDataBlock(self.data_in_block)
        for key, entry in self.data_in_block.items():
            if isinstance(entry, int):
                entry = [entry]
            for value in entry:
                assert await datablock.async_getValues(key, 1) == [value]
                key += 1

    async def test_sparse_datastore_check(self):
        """Test check frame."""
        datablock = ModbusSparseDataBlock(self.data_in_block)
        for key, entry in self.data_in_block.items():
            if isinstance(entry, int):
                entry = [entry]
            for value in entry:
                assert await datablock.async_getValues(key, 1) == [value]
                key += 1

    async def test_sparse_datastore_get(self):
        """Test check frame."""
        datablock = ModbusSparseDataBlock()
        assert await datablock.async_getValues(117) == ExcCodes.ILLEGAL_ADDRESS

    async def test_sparse_datastore_set(self):
        """Test check frame."""
        datablock = ModbusSparseDataBlock(self.data_in_block)
        assert not await datablock.async_setValues(1, {1: 5})
        assert not await datablock.async_setValues(1, [5])
        assert not await datablock.async_setValues(1, 5)

    async def test_sparse_datastore_async_set(self):
        """Test check frame."""
        datablock = ModbusSparseDataBlock(self.data_in_block)
        assert not await datablock.async_setValues(1, [5])

    async def test_sparse_datastore_set_not_ok(self):
        """Test check frame."""
        datablock = ModbusSparseDataBlock(self.data_in_block, mutable=False)
        with pytest.raises(ParameterException):
            await datablock.async_setValues(1, {7: 5})
        with pytest.raises(ParameterException):
            await datablock.async_setValues(1, [2, 3, 4])
        datablock = ModbusSparseDataBlock(self.data_in_block)
        datablock._process_values = mock.Mock(side_effect=KeyError)  # type: ignore[method-assign]
        assert await datablock.async_setValues(30, {17: 0}) == ExcCodes.ILLEGAL_ADDRESS
