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

    @pytest.mark.parametrize(
        ("exc", "text"),
        [
            (ModbusException("bad base"), "bad base"),
            (ModbusIOException("bad register"), "[Input/Output] bad register"),
            (ParameterException("bad parameter"), "[Invalid Parameter] bad parameter"),
            (NotImplementedException("bad function"), "[Not Implemented] bad function"),
            (ConnectionException("bad connection"), "[Connection] bad connection"),
            (NoSuchIdException("no id"), "[No Such id] no id"),
            (
                MessageRegisterException("Wrong message"),
                "[Error registering message] Wrong message",
            ),
            (ParameterException(), "[Invalid Parameter] "),
        ],
    )
    def test_exception_text(self, exc, text):
        """Test the text of each exception, including its category."""
        assert exc.string == text
        assert exc.args == (text,)
        assert str(exc) == f"Modbus Error: {text}"

    def test_io_exception_message(self):
        """Test ModbusIOException keeps its message attribute."""
        assert (
            ModbusIOException("bad register").message == "[Input/Output] bad register"
        )

    def test_is_error(self):
        """Test is_error()."""
        assert self.exceptions[0].isError()
