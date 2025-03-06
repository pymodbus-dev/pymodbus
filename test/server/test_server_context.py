"""Test server context."""
import pytest

from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext
from pymodbus.exceptions import NoSuchIdException


class TestServerSingleContext:
    """This is the test for the pymodbus.datastore.ModbusServerContext using a single device context."""

    device = ModbusDeviceContext()
    context = None

    def setup_method(self):
        """Set up the test environment."""
        self.context = ModbusServerContext(devices=self.device, single=True)

    def test_single_context_gets(self):
        """Test getting on a single context."""
        for dev_id in range(0, 0xFF):
            assert self.device == self.context[dev_id]

    def test_single_context_deletes(self):
        """Test removing on multiple context."""

        def _test():
            del self.context[0x00]

        with pytest.raises(NoSuchIdException):
            _test()

    def test_single_context_iter(self):
        """Test iterating over a single context."""
        expected = (0, self.device)
        for device in self.context:
            assert device == expected

    def test_single_context_default(self):
        """Test that the single context default values work."""
        self.context = ModbusServerContext()
        device = self.context[0x00]
        assert not device

    def test_single_context_set(self):
        """Test a setting a single device context."""
        device = ModbusDeviceContext()
        self.context[0x00] = device
        actual = self.context[0x00]
        assert device == actual

    def test_single_context_register(self):
        """Test single context register."""
        request_db = [1, 2, 3]
        device = ModbusDeviceContext()
        device.register(0xFF, "custom_request", request_db)
        assert device.store["custom_request"] == request_db
        assert device.decode(0xFF) == "custom_request"


class TestServerMultipleContext:
    """This is the test for the pymodbus.datastore.ModbusServerContext using multiple device contexts."""

    devices = None
    context = None

    def setup_method(self):
        """Set up the test environment."""
        self.devices = {id: ModbusDeviceContext() for id in range(10)}
        self.context = ModbusServerContext(devices=self.devices, single=False)

    def test_multiple_context_gets(self):
        """Test getting on multiple context."""
        for dev_id in range(0, 10):
            assert self.devices[dev_id] == self.context[dev_id]

    def test_multiple_context_deletes(self):
        """Test removing on multiple context."""
        del self.context[0x00]
        with pytest.raises(NoSuchIdException):
            self.context[0x00]()

    def test_multiple_context_iter(self):
        """Test iterating over multiple context."""
        for dev_id, device in self.context:
            assert device == self.devices[dev_id]
            assert dev_id in self.context

    def test_multiple_context_default(self):
        """Test that the multiple context default values work."""
        self.context = ModbusServerContext(single=False)
        with pytest.raises(NoSuchIdException):
            self.context[0x00]()

    def test_multiple_context_set(self):
        """Test a setting multiple device contexts."""
        devices = {id: ModbusDeviceContext() for id in range(10)}
        for dev_id, device in iter(devices.items()):
            self.context[dev_id] = device
        for dev_id, device in iter(devices.items()):
            actual = self.context[dev_id]
            assert device == actual
