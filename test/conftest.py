"""Configure pytest."""
import asyncio
import os
import platform
import sys
from collections import deque
from threading import enumerate as thread_enumerate
from unittest import mock

import pytest
import pytest_asyncio

from pymodbus.datastore import ModbusBaseSlaveContext
from pymodbus.server import ServerAsyncStop
from pymodbus.transport import NULLMODEM_HOST, CommParams, CommType, ModbusProtocol
from pymodbus.transport.transport import NullModem


sys.path.extend(["examples", "../examples", "../../examples"])

from examples.server_async import (  # pylint: disable=wrong-import-position
    run_async_server,
    setup_server,
)


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
    "TestNetwork": 8300,
}


@pytest.fixture(name="base_ports", scope="package")
def get_base_ports():
    """Return base_ports."""
    return BASE_PORTS


@pytest.fixture(name="use_comm_type")
def prepare_dummy_use_comm_type():
    """Return default comm_type."""
    return CommType.TCP


@pytest.fixture(name="use_host")
def define_use_host():
    """Set default host."""
    return NULLMODEM_HOST


@pytest.fixture(name="use_cls")
def prepare_commparams_server(use_port, use_host, use_comm_type):
    """Prepare CommParamsClass object."""
    if use_host == NULLMODEM_HOST and use_comm_type == CommType.SERIAL:
        use_host = f"{NULLMODEM_HOST}:{use_port}"
    return CommParams(
        comm_name="test comm",
        comm_type=use_comm_type,
        reconnect_delay=0,
        reconnect_delay_max=0,
        timeout_connect=0,
        source_address=(use_host, use_port),
        baudrate=9600,
        bytesize=8,
        parity="E",
        stopbits=2,
    )


@pytest.fixture(name="use_clc")
def prepare_commparams_client(use_port, use_host, use_comm_type):
    """Prepare CommParamsClass object."""
    if use_host == NULLMODEM_HOST and use_comm_type == CommType.SERIAL:
        use_host = f"{NULLMODEM_HOST}:{use_port}"
    timeout = 10 if not pytest.IS_WINDOWS else 2
    return CommParams(
        comm_name="test comm",
        comm_type=use_comm_type,
        reconnect_delay=0.1,
        reconnect_delay_max=0.35,
        timeout_connect=timeout,
        host=use_host,
        port=use_port,
        baudrate=9600,
        bytesize=8,
        parity="E",
        stopbits=2,
    )


@pytest.fixture(name="client")
def prepare_protocol(use_clc):
    """Prepare transport object."""
    transport = ModbusProtocol(use_clc, False)
    transport.callback_connected = mock.Mock()
    transport.callback_disconnected = mock.Mock()
    transport.callback_data = mock.Mock(return_value=0)
    if use_clc.comm_type == CommType.TLS:
        cwd = os.path.dirname(__file__) + "/../examples/certificates/pymodbus."
        transport.comm_params.sslctx = use_clc.generate_ssl(
            False, certfile=cwd + "crt", keyfile=cwd + "key"
        )
    if use_clc.comm_type == CommType.SERIAL:
        transport.comm_params.host = f"socket://localhost:{transport.comm_params.port}"
    return transport


@pytest.fixture(name="server")
def prepare_transport_server(use_cls):
    """Prepare transport object."""
    transport = ModbusProtocol(use_cls, True)
    transport.callback_connected = mock.Mock()
    transport.callback_disconnected = mock.Mock()
    transport.callback_data = mock.Mock(return_value=0)
    if use_cls.comm_type == CommType.TLS:
        cwd = os.path.dirname(__file__) + "/../examples/certificates/pymodbus."
        transport.comm_params.sslctx = use_cls.generate_ssl(
            True, certfile=cwd + "crt", keyfile=cwd + "key"
        )
    return transport


class DummyProtocol(ModbusProtocol):
    """Use in connection_made calls."""

    def __init__(self, is_server=False):  # pylint: disable=super-init-not-called
        """Initialize."""
        self.comm_params = CommParams()
        self.transport = None
        self.is_server = is_server
        self.is_closing = False
        self.data = b""
        self.connection_made = mock.Mock()
        self.connection_lost = mock.Mock()
        self.reconnect_task: asyncio.Task = None

    def handle_new_connection(self):
        """Handle incoming connect."""
        if not self.is_server:
            # Clients reuse the same object.
            return self
        return DummyProtocol()

    def close(self):
        """Simulate close."""
        self.is_closing = True

    def data_received(self, data):
        """Call when some data is received."""
        self.data += data


@pytest.fixture(name="dummy_protocol")
def prepare_dummy_protocol():
    """Return transport object."""
    return DummyProtocol


@pytest.fixture(name="mock_clc")
def define_commandline_client(
    use_comm,
    use_framer,
    use_port,
    use_host,
):
    """Define commandline."""
    my_port = str(use_port)
    cmdline = ["--comm", use_comm, "--framer", use_framer, "--timeout", "0.1"]
    if use_comm == "serial":
        if use_host == NULLMODEM_HOST:
            use_host = f"{use_host}:{my_port}"
        else:
            use_host = f"socket://{use_host}:{my_port}"
        cmdline.extend(["--baudrate", "9600", "--port", use_host])
    else:
        cmdline.extend(["--port", my_port, "--host", use_host])
    return cmdline


@pytest.fixture(name="mock_cls")
def define_commandline_server(
    use_comm,
    use_framer,
    use_port,
    use_host,
):
    """Define commandline."""
    my_port = str(use_port)
    cmdline = [
        "--comm",
        use_comm,
        "--framer",
        use_framer,
    ]
    if use_comm == "serial":
        if use_host == NULLMODEM_HOST:
            use_host = f"{use_host}:{my_port}"
        else:
            use_host = f"socket://{use_host}:{my_port}"
        cmdline.extend(["--baudrate", "9600", "--port", use_host])
    else:
        cmdline.extend(["--port", my_port, "--host", use_host])
    return cmdline


@pytest_asyncio.fixture(name="mock_server")
async def _run_server(
    mock_cls,
):
    """Run server."""
    run_args = setup_server(cmdline=mock_cls)
    task = asyncio.create_task(run_async_server(run_args))
    task.set_name("mock_server")
    await asyncio.sleep(0.1)
    yield mock_cls
    await ServerAsyncStop()
    task.cancel()
    await task


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
