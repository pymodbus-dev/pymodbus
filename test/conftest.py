"""Configure pytest."""
import functools
import platform
from collections import deque

import pytest

from pymodbus.datastore import ModbusBaseSlaveContext


def pytest_configure():
    """Configure pytest."""
    pytest.IS_DARWIN = platform.system().lower() == "darwin"
    pytest.IS_WINDOWS = platform.system().lower() == "windows"


# -----------------------------------------------------------------------#
# Generic fixtures
# -----------------------------------------------------------------------#


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

    def __init__(self):
        """Initialize."""
        self.data = None
        self.in_waiting = 0

    def mock_store(self, msg):
        """Store message."""
        self.data = msg
        self.in_waiting = len(self.data)

    def mock_retrieve(self, size):
        """Get message."""
        if not self.data or not size:
            return b""
        if size >= len(self.data):
            retval = self.data
        else:
            retval = self.data[0:size]
        self.data = None
        self.in_waiting = 0
        return retval

    def close(self):
        """Close."""
        return True

    def recv(self, size):
        """Receive."""
        return self.mock_retrieve(size)

    def read(self, size):
        """Read."""
        return self.mock_retrieve(size)

    def send(self, msg):
        """Send."""
        self.mock_store(msg)
        return len(msg)

    def recvfrom(self, size):
        """Receive from."""
        return [self.mock_retrieve(size)]

    def sendto(self, msg, *_args):
        """Send to."""
        self.mock_store(msg)
        return len(msg)

    def setblocking(self, _flag):
        """Set blocking."""
        return None

class mockSocket2:  # pylint: disable=invalid-name
    """Mock socket."""

    timeout = 2

    def __init__(self):
        """Initialize."""
        self.receive = deque()
        self.send = deque()

    def mock_prepare_receive(self, msg):
        """Store message."""
        self.receive.append(msg);

    def mock_read_sent(self):
        self.send.popleft()

    def mock_retrieve(self, size):
        """Get message."""
        if len(self.receive) == 0 or not size: 
            return b"";
        if size >= len(self.receive[0]):
            retval = self.receive.popleft()
        else:
            retval = self.receive[0][0:size]
            self.data[0] = self.receive[0][size:-1]
        return retval

    def close(self):
        """Close."""
        return True

    def recv(self, size):
        """Receive."""
        return self.mock_retrieve(size)

    def read(self, size):
        """Read."""
        return self.mock_retrieve(size)

    def send(self, msg):
        """Send."""
        self.mock_store(msg)
        return len(msg)

    def recvfrom(self, size):
        """Receive from."""
        return [self.mock_retrieve(size)]

    def sendto(self, msg, *_args):
        """Send to."""
        self.send.append(msg)
        return len(msg)

    def setblocking(self, _flag):
        """Set blocking."""
        return None


def run_coroutine(coro):
    """Run a coroutine as top-level task by iterating through all yielded steps."""
    result = None
    try:
        # step through all parts of coro without scheduling anything else:
        while True:
            result = coro.send(result)
    except StopIteration as exc:
        # coro reached end pass on its return value:
        return exc.value


def _yielded_return(_return_value, *_args):
    """Return Generator factory function with return value."""

    async def _():
        """Actual generator producing value."""
        # yield

    # return new generator each time this function is called:
    return _()


def return_as_coroutine(return_value=None):
    """Create a function that behaves like an asyncio coroutine and returns the given value.

    Typically used as a side effect of a mocked coroutine like this:

        # in module mymod:
        @asyncio.coroutine
        def my_coro_under_test():
            yield from asyncio.sleep(1)
            yield from asyncio.sleep(2)
            return 42

        # in test module:
        @mock.patch("mymod.asyncio.sleep")
        def test_it(mock_sleep):
            mock_sleep.side_effect = return_as_coroutine()
            result = run_coroutine(my_coro_under_test)
    """
    return functools.partial(_yielded_return, return_value)
