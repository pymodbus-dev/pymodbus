"""Test datastore context."""
import pytest

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.datastore.context import NoSuchIdException


class TestContextDataStore:
    """Unittest for the pymodbus.datastore.remote module."""

    async def test_datastore_device_Values(self):
        """Test ModbusDeviceContext."""
        dev = ModbusDeviceContext()
        await dev.async_OLD_getValues(0x01, 0x05)
        await dev.async_OLD_setValues(0x05, 0x05, [17])

    async def test_datastore_device_not_ok(self):
        """Test ModbusDeviceContext."""
        block = ModbusSequentialDataBlock(1, [17] * 8)
        dev = ModbusDeviceContext(di=block, co=block, hr=block, ir=block)
        await dev.async_OLD_getValues(0x03, 0x05)
        await dev.async_OLD_setValues(0x05, 0x05, [17])

    def test_datastore_server(self):
        """Test ModbusServerContext."""
        dev = ModbusServerContext()
        str(dev)
        dev = ModbusServerContext(devices={})
        dev = ModbusServerContext(single=False)
        dev = ModbusServerContext(devices={1: {}}, single=False)

    def test_datastore_server_ids(self):
        """Test ModbusServerContext."""
        srv = ModbusServerContext()
        assert isinstance(srv.device_ids(), list)

    async def test_datastore_server_device_id(self):
        """Test ModbusServerContext."""
        block = ModbusSequentialDataBlock(1, [17] * 8)
        dev = ModbusDeviceContext(di=block, co=block, hr=block, ir=block)
        srv = ModbusServerContext(devices={1: dev}, single=False)
        assert srv.device_ids() == [1]
        await srv.async_setValues(1, 0x05, 0, [1])
        assert await srv.async_getValues(1, 0x03, 0) == [1]
        with pytest.raises(NoSuchIdException):
            await srv.async_getValues(15, 0, 0)
