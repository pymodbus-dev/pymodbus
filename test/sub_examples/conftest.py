"""Fixtures for examples tests."""
import asyncio
import sys

import pytest_asyncio

from pymodbus.server import ServerAsyncStop


sys.path.extend(["examples", "../examples", "../../examples"])

from examples.server_async import (  # noqa: E402  # pylint: disable=wrong-import-position
    run_async_server,
    setup_server,
)


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
