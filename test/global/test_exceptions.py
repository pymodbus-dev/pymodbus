"""Test exceptions."""
import pytest

from pymodbus.exceptions import (
    ConnectionException,
    MessageRegisterException,
    ModbusException,
    ModbusIOException,
    NoSuchIdException,
    NotImplementedException,
    ParameterException,
)


class TestExceptions:  # pylint: disable=too-few-public-methods
    """Unittest for the pymodbus.exceptions module."""

    exceptions = [
        ModbusException("bad base"),
        ModbusIOException("bad register"),
        ParameterException("bad parameter"),
        NotImplementedException("bad function"),
        ConnectionException("bad connection"),
        NoSuchIdException("no id"),
        MessageRegisterException("Wrong message"),
    ]

    def test_exceptions(self):
        """Test all module exceptions."""
        for exc in self.exceptions:
            with pytest.raises(ModbusException, match="Modbus Error:"):
                raise exc

    def test_is_error(self):
        """Test is_error()."""
        assert self.exceptions[0].isError()
