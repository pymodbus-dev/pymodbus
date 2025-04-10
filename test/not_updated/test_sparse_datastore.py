"""Test framers."""

import pytest

from pymodbus.datastore import ModbusSparseDataBlock


@pytest.mark.asyncio
async def test_check_async_sparsedatastore():
    """Test check frame."""
    data_in_block = {
        1: 6720,
        2: 130,
        30: [0x0D, 0xFE],
        105: [1, 2, 3, 4],
        20000: [45, 241, 48],
        20008: 38,
        48140: [0x4208, 0xCCCD],
    }
    datablock = ModbusSparseDataBlock(data_in_block)
    for key, entry in data_in_block.items():
        if isinstance(entry, int):
            entry = [entry]
        for value in entry:
            assert await datablock.async_getValues(key, 1) == [value]
            key += 1


def test_check_sparsedatastore():
    """Test check frame."""
    data_in_block = {
        1: 6720,
        2: 130,
        30: [0x0D, 0xFE],
        105: [1, 2, 3, 4],
        20000: [45, 241, 48],
        20008: 38,
        48140: [0x4208, 0xCCCD],
    }
    datablock = ModbusSparseDataBlock(data_in_block)
    for key, entry in data_in_block.items():
        if isinstance(entry, int):
            entry = [entry]
        for value in entry:
            assert datablock.getValues(key, 1) == [value]
            key += 1
