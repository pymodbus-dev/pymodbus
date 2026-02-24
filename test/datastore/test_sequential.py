"""Test framers."""

from pymodbus.constants import ExcCodes
from pymodbus.datastore import ModbusSequentialDataBlock


class TestCOntextDataStore:
    """Unittest for the pymodbus.datastore.remote module."""

    def test_datastore_Sequential(self):
        """Test ModbusDeviceContext."""
        ModbusSequentialDataBlock(0x01, [17])
        ModbusSequentialDataBlock(0x01, 17)

    async def test_datastore_Sequential_get_0K(self):
        """Test ModbusDeviceContext."""
        block = ModbusSequentialDataBlock(0x01, [17])
        assert await block.async_OLD_getValues(1) == [17]

    async def test_datastore_Sequential_get(self):
        """Test ModbusDeviceContext."""
        block = ModbusSequentialDataBlock(0x01, [17])
        assert await block.async_OLD_getValues(13) == ExcCodes.ILLEGAL_ADDRESS

    async def test_datastore_Sequential_set(self):
        """Test ModbusDeviceContext."""
        block = ModbusSequentialDataBlock(0x01, [17])
        await block.async_OLD_setValues(1, [19])
        await block.async_OLD_setValues(1, 19)
        assert await block.async_OLD_setValues(13, [17]) == ExcCodes.ILLEGAL_ADDRESS
