"""Test datastore context."""
import pytest

from pymodbus.datastore import (
    ModbusBaseDeviceContext,
    ModbusDeviceContext,
    ModbusServerContext,
)
from pymodbus.exceptions import NoSuchIdException


class TestContextDataStore:
    """Unittest for the pymodbus.datastore.remote module."""

    async def test_datastore_base_device(self):
        """Test ModbusDeviceContext."""
        dev = ModbusBaseDeviceContext()
        await dev.async_getValues(0x01, 0x01)
        await dev.async_setValues(0x05, 0x01, [0])

    def test_datastore_device(self):
        """Test ModbusDeviceContext."""
        dev = ModbusDeviceContext()
        str(dev)
        dev.reset()

    async def test_datastore_device_Values(self):
        """Test ModbusDeviceContext."""
        dev = ModbusDeviceContext()
        await dev.async_getValues(0x01, 0x05)
        await dev.async_setValues(0x05, 0x05, [17])

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

    def test_datastore_get(self):
        """Test ModbusServerContext."""
        server = ModbusServerContext(devices={1: {}}, single=False)
        with pytest.raises(NoSuchIdException):
            server[5]
        server = ModbusServerContext(devices={1: {}, 0: {}}, single=False)
        assert isinstance(server[5], dict)
        server = ModbusServerContext(devices={1: {}}, single=True)
        assert isinstance(server[5], dict)

