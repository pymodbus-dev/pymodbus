"""Configure pytest."""
import asyncio
import platform
import sys
from collections import deque
from threading import enumerate as thread_enumerate

import pytest

from pymodbus.datastore import ModbusBaseSlaveContext
from pymodbus.transport.transport import NullModem


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
    "TestCommModbusProtocol": 7305,
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
    """Return base_ports."""
    return BASE_PORTS


@pytest.fixture(name="system_health_check", autouse=True)
async def _check_system_health():
    """Check Thread, asyncio.task and NullModem for leftovers."""
    if task := asyncio.current_task():
        task.set_name("main loop")
    start_threads = {thread.getName(): thread for thread in thread_enumerate()}
    start_tasks = {task.get_name(): task for task in asyncio.all_tasks()}
    yield
    await asyncio.sleep(0.1)
    for count in range(10):
        all_clean = True
        error_text = f"ERROR tasks/threads hanging after {count} retries:\n"
        for thread in thread_enumerate():
            name = thread.getName()
            if not (
                name in start_threads
                or name.startswith("asyncio_")
                or (sys.version_info.minor == 8 and name.startswith("ThreadPoolExecutor"))
            ):
                thread.join(1.0)
                error_text += f"-->THREAD{name}: {thread}\n"
                all_clean = False
        for task in asyncio.all_tasks():
            name = task.get_name()
            if not (name in start_tasks or "wrap_asyncgen_fixture" in str(task)):
                task.cancel()
                error_text += f"-->TASK{name}: {task}\n"
                all_clean = False
        if all_clean:
            break
        await asyncio.sleep(0.3)
    assert all_clean, error_text
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
