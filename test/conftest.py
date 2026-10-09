"""Configure pytest."""

import asyncio
import platform
import sys
from collections import deque
from threading import enumerate as thread_enumerate
from typing import cast
from unittest import mock

import pytest
import pytest_asyncio
from serialx import SerialException, SerialTimeoutException

from pymodbus.constants import ExcCodes
from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext
from pymodbus.server import ServerAsyncStop
from pymodbus.transport import NULLMODEM_HOST, CommParams, CommType
from pymodbus.transport.transport import NullModem


sys.path.extend(["examples", "../examples", "../../examples"])

from examples.server_async import (  # pylint: disable=wrong-import-position
    run_async_server,
    setup_server,
)


def pytest_configure():
    """Configure pytest."""


# -----------------------------------------------------------------------#
# Generic fixtures
# -----------------------------------------------------------------------#
BASE_PORTS = {
    "TestTransportNullModem": 7100,
    "TestTransportNullModemComm": 7150,
    "TestTransportProtocol1": 7200,
    "TestTransportProtocol2": 7300,
    "TestTransportSerial": 7400,
    "TestTransportReconnect": 7500,
    "TestTransportComm": 7600,
    "TestMessage": 7700,
    "TestExamples": 7800,
    "TestAsyncExamples": 7900,
    "TestSyncExamples": 8000,
    "TestModbusProtocol": 8100,
    "TestClientServerSyncExamples": 8300,
    "TestClientServerAsyncExamples": 8400,
    "TestNetwork": 8500,
    "TestSimulator": 8600,
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
    timeout = 10 if platform.system().lower() != "windows" else 2
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


@pytest.fixture(name="mock_clc")
def define_commandline_client(
    use_comm,
    use_framer,
    use_port,
    use_host,
):
    """Define commandline."""
    my_port = str(use_port)
    # Socket-backed serial can take seconds to complete long RTU frames under load.
    x_parm = "serial" if use_comm.startswith("serial") else use_comm
    timeout = "10" if use_comm.startswith("serial") else "0.1"
    cmdline = ["--comm", x_parm, "--framer", use_framer, "--timeout", timeout]
    if use_comm.startswith("serial"):
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
    x_parm = "serial" if use_comm.startswith("serial") else use_comm
    cmdline = [
        "--comm",
        x_parm,
        "--framer",
        use_framer,
    ]
    if use_comm.startswith("serial"):
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
    start_threads = {thread.name: thread for thread in thread_enumerate()}
    start_tasks = {task.get_name(): task for task in asyncio.all_tasks()}
    yield
    await asyncio.sleep(0.1)
    all_clean = True
    error_text = ""
    for count in range(10):
        all_clean = True
        error_text = f"ERROR tasks/threads hanging after {count} retries:\n"
        for thread in thread_enumerate():
            name = thread.name
            if not (
                name in start_threads
                or name.startswith("asyncio_")
                or (
                    sys.version_info.minor == 8
                    and name.startswith("ThreadPoolExecutor")
                )
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


@pytest.fixture(name="mock_server_context")
def define_mock_servercontext() -> ModbusServerContext:
    """Define context class."""

    class MockServerContext(ModbusServerContext):
        """Mock context."""

        def __init__(self, valid=False, default=True):
            """Initialize."""
            super().__init__(devices=ModbusDeviceContext())
            self.valid = valid
            self.default = default

        async def async_getValues(self, device_id, func_code, address, count=0):
            """Get values."""
            _ = device_id, func_code, address
            if count > 0x100:
                return ExcCodes.ILLEGAL_VALUE
            return [self.default] * count

        async def async_setValues(self, device_id, func_code, address, values):
            """Set values."""

    return cast(ModbusServerContext, MockServerContext)


class MockLastValuesContext(ModbusServerContext):
    """Mock context."""

    def __init__(self, valid=False, default=True):
        """Initialize."""
        super().__init__(devices=ModbusDeviceContext())
        self.valid = valid
        self.default = default
        self.last_values: list = []

    async def async_getValues(self, device_id, func_code, address, count=0):
        """Get values."""
        _ = device_id, func_code, address
        return [self.default] * count

    async def async_setValues(self, device_id, func_code, address, values):
        """Set values."""
        _ = device_id, func_code, address
        self.last_values = values


class mockSocket:  # pylint: disable=invalid-name
    """Mock socket."""

    timeout = 2

    def __init__(self, copy_send=True):
        """Initialize."""
        self.packets = deque()
        self.buffer = None
        self.in_waiting = 0
        self.prop_write_timeout = 0
        self.copy_send = copy_send
        self.state_open = False

    def mock_prepare_receive(self, msg):
        """Store message."""
        self.packets.append(msg)
        self.in_waiting += len(msg)

    def close(self):
        """Close."""
        self.state_open = False
        return True

    def open(self):
        """Close."""
        self.state_open = True
        return True

    def recv(self, size):
        """Receive."""
        if not self.packets or not size:
            return b""
        retval = self.packets.popleft()
        self.in_waiting -= len(retval)
        return retval

    def read(self, size):
        """Read."""
        return self.recv(size)

    def recvfrom(self, size):
        """Receive from."""
        return [self.recv(size)]

    def write(self, msg):
        """Write."""
        return self.send(msg)

    def send(self, msg):
        """Send."""
        if not self.copy_send:
            return len(msg)
        self.packets.append(msg)
        self.in_waiting += len(msg)
        return len(msg)

    @property
    def is_open(self):
        """Open."""
        return self.state_open

    def sendto(self, msg, *_args):
        """Send to."""
        return self.send(msg)

    def setblocking(self, _flag):
        """Set blocking."""
        return None


@pytest.fixture(params=[True, False])
def mock_use_ser_2lib(request):
    """Patch select_import_serial."""
    with mock.patch(
        "pymodbus.transport.serialtransport.SerialInterface.select_import_serial",
        autospec=True,
    ) as mock_lib:
        mock_lib.return_value = request.param
        yield


@pytest.fixture
def mock_with_use_comm(use_comm):
    """Patch select_import_serial."""
    if not (old_lib := "1" in use_comm):
        old_lib = False if "2" in use_comm else None
    if old_lib is None:
        yield None
    else:
        with mock.patch(
            "pymodbus.transport.serialtransport.SerialInterface.select_import_serial",
            autospec=True,
        ) as mock_lib:
            mock_lib.return_value = old_lib
            yield mock_lib


@pytest.fixture
def mock_ser_intf():
    """Patch SerialInterface."""
    with (
        mock.patch(
            "pymodbus.transport.serialtransport.SerialInterface.select_import_serial",
            autospec=True,
        ) as mock_lib,
        mock.patch(
            "pymodbus.transport.serialtransport.serialx", autospec=True
        ) as mock_ser,
    ):
        mock_lib.return_value = False
        mock_ser.SerialException = SerialException
        mock_ser.SerialTimeoutException = SerialTimeoutException
        serial = mockSocket()
        mock_ser.serial_for_url.return_value = serial
        yield serial
