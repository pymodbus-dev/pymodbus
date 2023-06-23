"""Fixtures for examples tests."""
import asyncio

import pytest_asyncio

from examples.server_async import run_async_server, setup_server
from pymodbus.server import ServerAsyncStop
from pymodbus.transport.transport import NULLMODEM_HOST


@pytest_asyncio.fixture(name="port_offset")
def _define_port_offset():
    """Define port offset"""
    return 0


@pytest_asyncio.fixture(name="mock_clc")
def _define_commandline_client(
    use_comm,
    use_framer,
    use_port,
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
        cmdline.extend(["--port", f"{NULLMODEM_HOST}:{my_port}", "--baudrate", "9600"])
    else:
        cmdline.extend(["--port", my_port, "--host", NULLMODEM_HOST])
    return cmdline


@pytest_asyncio.fixture(name="mock_cls")
def _define_commandline_server(
    use_comm,
    use_framer,
    use_port,
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
        cmdline.extend(["--port", f"{NULLMODEM_HOST}:{my_port}", "--baudrate", "9600"])
    else:
        cmdline.extend(["--port", my_port, "--host", NULLMODEM_HOST])
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
