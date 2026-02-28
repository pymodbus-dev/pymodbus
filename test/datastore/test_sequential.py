"""Test framers."""

from pymodbus.datastore import ModbusSequentialDataBlock


class TestCOntextDataStore:
    """Unittest for the pymodbus.datastore.remote module."""

    def test_datastore_Sequential(self):
        """Test ModbusDeviceContext."""
        ModbusSequentialDataBlock(0x01, [17])
        ModbusSequentialDataBlock(0x01, 17)
