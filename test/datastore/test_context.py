"""Test framers."""
import pytest

from pymodbus.datastore import (
    ModbusBaseDeviceContext,
    ModbusDeviceContext,
    ModbusServerContext,
)
from pymodbus.exceptions import NoSuchIdException


class TestContextDataStore:
    """Unittest for the pymodbus.datastore.remote module."""

    def test_datastore_base_device(self):
        """Test ModbusDeviceContext."""
        dev = ModbusBaseDeviceContext()
        dev.getValues(0x01, 0x01)
        dev.setValues(0x05, 0x01, None)

    def test_datastore_device(self):
        """Test ModbusDeviceContext."""
        dev = ModbusDeviceContext()
        str(dev)
        dev.reset()

    def test_datastore_device_Values(self):
        """Test ModbusDeviceContext."""
        dev = ModbusDeviceContext()
        dev.getValues(0x01, 0x05)
        dev.setValues(0x05, 0x05, [17])

    def test_datastore_device_register(self):
        """Test ModbusDeviceContext."""
        dev = ModbusDeviceContext()
        dev.register(0x77, "device register test")

    def test_datastore_server(self):
        """Test ModbusServerContext."""
        dev = ModbusServerContext()
        str(dev)
        dev = ModbusServerContext(devices={})
        dev = ModbusServerContext(single=False)
        dev = ModbusServerContext(devices={1: {}}, single=False)

    def test_datastore_server_iter(self):
        """Test ModbusServerContext."""
        dev = ModbusServerContext()
        _ = list(dev)

    def test_datastore_server_contains(self):
        """Test ModbusServerContext."""
        dev = ModbusServerContext()
        assert 0 in dev
        dev2 = ModbusServerContext()
        dev2.single = False
        assert 0 in dev2

    def test_datastore_server_set(self):
        """Test ModbusServerContext."""
        dev = ModbusDeviceContext()
        srv = ModbusServerContext()
        srv[1] = dev
        srv.single = False
        srv[2] = dev
        del srv[2]
        with pytest.raises(NoSuchIdException):
            srv[2000] = dev
        with pytest.raises(NoSuchIdException):
            del srv[2000]

    def test_datastore_server_ids(self):
        """Test ModbusServerContext."""
        srv = ModbusServerContext()
        assert isinstance(srv.device_ids(), list)
