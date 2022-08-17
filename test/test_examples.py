#!/usr/bin/env python3
"""Test client async."""
import logging
import asyncio
from asyncio import CancelledError
from dataclasses import dataclass
import pytest

from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)

from examples.server_sync import run_server as server_sync
from examples.server_async import run_server as server_async
from examples.client_sync import (
    run_client as client_sync,
    setup_client as client_setup_sync,
)
from examples.client_async import (
    run_client as client_async,
    setup_client as client_setup_async,
)
from examples.client_sync_basic_calls import demonstrate_calls as demo_sync_basic
from examples.client_sync_extended_calls import demonstrate_calls as demo_sync_extended
from examples.client_async_basic_calls import demonstrate_calls as demo_async_basic
from examples.client_async_extended_calls import demonstrate_calls as demo_async_extended


_logger = logging.getLogger()

EXAMPLE_PATH = "../examples"
PYTHON = "python3"
TIMEOUT = 30


def to_be_solved(test_type, test_comm, test_framer):
    """Solve problems."""
    if test_comm == "serial":
        return True
    if test_comm == "tls":
        return True
    if test_type == "extended" and test_framer is ModbusRtuFramer:
        return True
    return False


@dataclass
class Commandline:
    """Simulate commandline parameters."""

    comm = None
    framer = None
    port = None

    store = "sequential"
    slaves = None
    modbus_calls = None


@pytest.mark.parametrize(
    "test_type",
    [
        "connect",
        "basic",
        "extended",
    ]
)
@pytest.mark.parametrize(
    "test_server, test_client",
    [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ]
)
@pytest.mark.parametrize(
    "test_comm, test_framer",
    [
        ("tcp", ModbusSocketFramer),
        ("tcp", ModbusRtuFramer),
        ("tls", ModbusTlsFramer),
        ("udp", ModbusSocketFramer),
        ("udp", ModbusRtuFramer),
        ("serial", ModbusRtuFramer),
        ("serial", ModbusAsciiFramer),
        ("serial", ModbusBinaryFramer),
    ]
)
async def test_client_server(test_type, test_server, test_client, test_comm, test_framer):  # pylint: disable=too-complex
    """Test client/server examples."""

    if to_be_solved(
        test_type,
        test_comm,
        test_framer,
    ):
        return

    args = Commandline()
    args.comm = test_comm
    args.framer = test_framer
    args.port = "/dev/ttyp0" if args.comm == "serial" else "5020"

    method_client = {
        "connect": (None, None),
        "basic": (demo_sync_basic, demo_async_basic),
        "extended": (demo_sync_extended, demo_async_extended),
    }

    _logger.setLevel("DEBUG")

    def handle_task(result):
        """Handle task exit."""
        try:
            result = result.result()
        except CancelledError:
            pass
        except Exception as exc:  # pylint: disable=broad-except
            pytest.fail(f"Exception in task serve_forever: {exc} ")

    loop = asyncio.get_event_loop()
    server = None
    task_sync = None
    task = None
    client = None
    not_ok_exc = None
    try:
        if test_server:
            server = server_sync(args=args)
            task_sync = loop.run_in_executor(None, server.serve_forever)
        else:
            server = await server_async(args=args)
            task = asyncio.create_task(server.serve_forever())
            task.add_done_callback(handle_task)
            assert not task.cancelled()
            await asyncio.wait_for(server.serving, timeout=0.1)
        await asyncio.sleep(0.1)

        if test_client:
            client = client_setup_sync(args=args)
            await asyncio.wait_for(loop.run_in_executor(None, client_sync, client, method_client[test_type][0]), TIMEOUT)
        else:
            client = client_setup_async(args=args)
            await asyncio.wait_for(client_async(client, modbus_calls=method_client[test_type][1]), TIMEOUT)
    except Exception as exc:  # pylint: disable=broad-except # noqa: E722
        not_ok_exc = f"Server/Client raised exception <<{exc}>>"

    if server:
        if test_server:
            server.shutdown()
        else:
            await server.shutdown()
    if task is not None:
        await asyncio.sleep(0.1)
        if not task.cancelled():
            task.cancel()
            try:
                await task
            except CancelledError:
                pass
            except Exception as exc:  # pylint: disable=broad-except
                pytest.fail(f"Exception in task serve_forever: {exc} ")
            task = None
    if task_sync:
        server.is_running = False
        while not task_sync.done():
            task_sync.cancel()
            await asyncio.sleep(0.1)
        assert task_sync.cancelled()
    if client:
        if test_client:
            client.close()
        else:
            await client.aClose()
    if not_ok_exc:
        pytest.fail(not_ok_exc)


if __name__ == "__main__":
    asyncio.run(test_client_server("connect", False, False, "udp", ModbusSocketFramer))
