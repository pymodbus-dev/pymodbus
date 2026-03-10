"""Test datastore context."""
import pytest

from pymodbus.constants import ExcCodes
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
        ModbusDeviceContext()

    async def test_datastore_device_not_ok(self):
        """Test ModbusDeviceContext."""
        block = ModbusSequentialDataBlock(1, [17] * 8)
        ModbusDeviceContext(di=block, co=block, hr=block, ir=block)

    def test_datastore_server(self):
        """Test ModbusServerContext."""
        dev = ModbusServerContext(devices=ModbusDeviceContext())
        str(dev)
        dev = ModbusServerContext(devices=ModbusDeviceContext())
        dev = ModbusServerContext(devices=ModbusDeviceContext(), single=False)
        dev = ModbusServerContext(devices={1: ModbusDeviceContext()}, single=False)
        with pytest.raises(TypeError):
            ModbusServerContext()

    def test_datastore_server_ids(self):
        """Test ModbusServerContext."""
        srv = ModbusServerContext(devices=ModbusDeviceContext())
        assert isinstance(srv.device_ids(), list)

    async def test_datastore_server_device_id(self):
        """Test ModbusServerContext."""
        block = ModbusSequentialDataBlock(1, [17] * 8)
        dev = ModbusDeviceContext(di=block, co=block, hr=block, ir=block)
        srv = ModbusServerContext(devices={1: dev}, single=False)
        assert srv.device_ids() == [1]
        await srv.async_setValues(1, 0x05, 0, [1])
        assert await srv.async_getValues(1, 0x03, 0) == ExcCodes.DEVICE_BUSY
        with pytest.raises(NoSuchIdException):
            await srv.async_getValues(15, 0, 0)


    async def test_datastore_server_device_id_0(self):
        """Test ModbusServerContext."""
        block = ModbusSequentialDataBlock(1, [17] * 8)
        dev = ModbusDeviceContext(di=block, co=block, hr=block, ir=block)
        srv = ModbusServerContext(devices={0: dev}, single=False)
        await srv.async_getValues(15, 0x03, 0)
