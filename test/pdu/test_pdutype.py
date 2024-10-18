"""Test pdu."""
import pytest

from pymodbus.exceptions import NotImplementedException
from pymodbus.pdu import (
    ExceptionResponse,
    ModbusExceptions,
    ModbusPDU,
)


class TestPduType:
    """Test all PDU types requests/responses."""

