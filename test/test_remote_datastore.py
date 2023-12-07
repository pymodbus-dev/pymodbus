"""Test remote datastore."""
from unittest import mock

import pytest

from pymodbus.bit_read_message import ReadCoilsResponse
from pymodbus.bit_write_message import WriteMultipleCoilsResponse
from pymodbus.datastore.remote import RemoteSlaveContext
from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import ExceptionResponse
from pymodbus.register_read_message import ReadInputRegistersResponse


class TestRemoteDataStore:
    """Unittest for the pymodbus.datastore.remote module."""

    def test_remote_slave_context(self):
        """Test a modbus remote slave context."""
        context = RemoteSlaveContext(None)
        assert str(context)
        with pytest.raises(NotImplementedException):
            context.reset()

    def test_remote_slave_set_values(self):
        """Test setting values against a remote slave context."""
        client = mock.MagicMock()
        client.write_coils = lambda a, b: WriteMultipleCoilsResponse()
        client.write_registers = lambda a, b: ExceptionResponse(0x10, 0x02)

        context = RemoteSlaveContext(client)
        context.setValues(0x0F, 0, [1])
        result = context.setValues(0x10, 1, [1])
        assert result.exception_code == 0x02
        assert result.function_code == 0x90

    def test_remote_slave_get_values(self):
        """Test getting values from a remote slave context."""
        client = mock.MagicMock()
        client.read_coils = lambda a, b: ReadCoilsResponse([1] * 10)
        client.read_input_registers = lambda a, b: ReadInputRegistersResponse([10] * 10)
        client.read_holding_registers = lambda a, b: ExceptionResponse(0x15)

        context = RemoteSlaveContext(client)
        context.validate(1, 0, 10)
        result = context.getValues(1, 0, 10)
        assert result == [1] * 10

        context.validate(4, 0, 10)
        result = context.getValues(4, 0, 10)
        assert result == [10] * 10

        context.validate(3, 0, 10)
        result = context.getValues(3, 0, 10)
        assert result != [10] * 10

    def test_remote_slave_validate_values(self):
        """Test validating against a remote slave context."""
        client = mock.MagicMock()
        client.read_coils = lambda a, b: ReadCoilsResponse([1] * 10)
        client.read_input_registers = lambda a, b: ReadInputRegistersResponse([10] * 10)
        client.read_holding_registers = lambda a, b: ExceptionResponse(0x15)

        context = RemoteSlaveContext(client)
        result = context.validate(1, 0, 10)
        assert result

        result = context.validate(4, 0, 10)
        assert result

        result = context.validate(3, 0, 10)
        assert result
