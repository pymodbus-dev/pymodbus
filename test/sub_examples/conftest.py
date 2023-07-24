"""Fixtures for examples tests."""
import asyncio

import pytest
import pytest_asyncio

from examples.server_async import run_async_server, setup_server
from pymodbus.server import ServerAsyncStop
from pymodbus.transport import NULLMODEM_HOST


@pytest.fixture(name="port_offset")
def define_port_offset():
    """Define port offset"""
    return 0


@pytest.fixture(name="use_host")
def define_use_host():
    """Set default host"""
    return NULLMODEM_HOST


@pytest.fixture(name="mock_clc")
def define_commandline_client(
    use_comm,
    use_framer,
    use_port,
    use_host,
    port_offset,
):
    """Define commandline."""
    my_port = str(use_port + port_offset)
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


@pytest.fixture(name="mock_cls")
def define_commandline_server(
    use_comm,
    use_framer,
    use_port,
    use_host,
    port_offset,
):
    """Define commandline."""
    my_port = str(use_port + port_offset)
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
    await asyncio.sleep(0.1)
    yield mock_cls
    await ServerAsyncStop()
    task.cancel()
    await task
