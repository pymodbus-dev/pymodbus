"""Configure pytest."""
import platform
from collections import deque

import pytest

from pymodbus.datastore import ModbusBaseSlaveContext
from pymodbus.transport import NullModem


def pytest_configure():
    """Configure pytest."""
    pytest.IS_DARWIN = platform.system().lower() == "darwin"
    pytest.IS_WINDOWS = platform.system().lower() == "windows"


# -----------------------------------------------------------------------#
# Generic fixtures
# -----------------------------------------------------------------------#
BASE_PORTS = {
    "TestBasicModbusProtocol": 7100,
    "TestBasicSerial": 7200,
    "TestCommModbusProtocol": 7300,
    "TestCommNullModem": 7400,
    "TestExamples": 7500,
    "TestAsyncExamples": 7600,
    "TestSyncExamples": 7700,
    "TestModbusProtocol": 7800,
    "TestNullModem": 7900,
    "TestReconnectModbusProtocol": 8000,
    "TestClientServerSyncExamples": 8100,
    "TestClientServerAsyncExamples": 8200,
}


@pytest.fixture(name="base_ports", scope="package")
def get_base_ports():
    """Return base_ports"""
    return BASE_PORTS


@pytest.fixture(name="nullmodem_check", autouse=True)
def _check_nullmodem():
    """Check null modem."""
    yield
    assert not NullModem.is_dirty()


class MockContext(ModbusBaseSlaveContext):
    """Mock context."""

    def __init__(self, valid=False, default=True):
        """Initialize."""
        self.valid = valid
        self.default = default

    def validate(self, _fc, _address, _count=0):
        """Validate values."""
        return self.valid

    def getValues(self, _fc, _address, count=0):
        """Get values."""
        return [self.default] * count

    def setValues(self, _fc, _address, _values):
        """Set values."""


class MockLastValuesContext(ModbusBaseSlaveContext):
    """Mock context."""

    def __init__(self, valid=False, default=True):
        """Initialize."""
        self.valid = valid
        self.default = default
        self.last_values = []

    def validate(self, _fc, _address, _count=0):
        """Validate values."""
        return self.valid

    def getValues(self, _fc, _address, count=0):
        """Get values."""
        return [self.default] * count

    def setValues(self, _fc, _address, values):
        """Set values."""
        self.last_values = values


class FakeList:
    """Todo, replace with magic mock."""

    def __init__(self, size):
        """Initialize."""
        self.size = size

    def __len__(self):
        """Get length."""
        return self.size

    def __iter__(self):
        """Iterate."""


class mockSocket:  # pylint: disable=invalid-name
    """Mock socket."""

    timeout = 2

    def __init__(self, copy_send=True):
        """Initialize."""
        self.packets = deque()
        self.buffer = None
        self.in_waiting = 0
        self.copy_send = copy_send

    def mock_prepare_receive(self, msg):
        """Store message."""
        self.packets.append(msg)
        self.in_waiting += len(msg)

    def close(self):
        """Close."""
        return True

    def recv(self, size):
        """Receive."""
        if not self.packets or not size:
            return b""
        if not self.buffer:
            self.buffer = self.packets.popleft()
        if size >= len(self.buffer):
            retval = self.buffer
            self.buffer = None
        else:
            retval = self.buffer[0:size]
            self.buffer = self.buffer[size]
        self.in_waiting -= len(retval)
        return retval

    def read(self, size):
        """Read."""
        return self.recv(size)

    def recvfrom(self, size):
        """Receive from."""
        return [self.recv(size)]

    def send(self, msg):
        """Send."""
        if not self.copy_send:
            return len(msg)
        self.packets.append(msg)
        self.in_waiting += len(msg)
        return len(msg)

    def sendto(self, msg, *_args):
        """Send to."""
        return self.send(msg)

    def setblocking(self, _flag):
        """Set blocking."""
        return None


_CURRENT_PORT = 5200


@pytest.fixture(name="use_port")
def get_port():
    """Get next port."""
    global _CURRENT_PORT  # pylint: disable=global-statement
    _CURRENT_PORT += 1
    return _CURRENT_PORT
