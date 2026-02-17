"""Test framers."""

from pymodbus.constants import ExcCodes
from pymodbus.datastore import ModbusSequentialDataBlock


class TestCOntextDataStore:
    """Unittest for the pymodbus.datastore.remote module."""

    def test_datastore_Sequential(self):
        """Test ModbusDeviceContext."""
        ModbusSequentialDataBlock(0x01, [17])
        ModbusSequentialDataBlock(0x01, 17)
        ModbusSequentialDataBlock(0x01, 17).default(112)

    def test_datastore_Sequential_get(self):
        """Test ModbusDeviceContext."""
        block = ModbusSequentialDataBlock(0x01, [17])
        assert block.getValues(13) == ExcCodes.ILLEGAL_ADDRESS

    def test_datastore_Sequential_set(self):
        """Test ModbusDeviceContext."""
        block = ModbusSequentialDataBlock(0x01, [17])
        block.setValues(1, [19])
        block.setValues(1, 19)
        assert block.setValues(13, [17]) == ExcCodes.ILLEGAL_ADDRESS

    def test_datastore_Sequential_iter(self):
        """Test check frame."""
        block = ModbusSequentialDataBlock(0x01, [17])
        str(block)
        _ = list(block)
