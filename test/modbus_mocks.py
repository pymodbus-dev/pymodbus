"""Modbus mocks."""
from pymodbus.interfaces import IModbusSlaveContext

# ---------------------------------------------------------------------------#
#  Mocks
# ---------------------------------------------------------------------------#


class mock:  # pylint: disable=too-few-public-methods,invalid-name
    """Mock."""


class MockContext(IModbusSlaveContext):
    """Mock context."""

    def __init__(self, valid=False, default=True):
        """Initialize."""
        self.valid = valid
        self.default = default

    def validate(self, fx, address, count=0):
        """Validate values."""
        return self.valid

    def getValues(self, fx, address, count=0):
        """Get values."""
        return [self.default] * count

    def setValues(self, fx, address, values):
        """Set values."""


class FakeList:
    """Todo, replace with magic mock."""

    def __init__(self, size):
        """Initialize."""
        self.size = size

    def __len__(self):
        """Get length."""
        return self.size

    def __iter__(self):  # pylint: disable=non-iterator-returned
        """Iterate."""
        return []
