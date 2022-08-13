#!/usr/bin/env python3
"""Test client async."""
import logging
import asyncio
from dataclasses import dataclass
import pytest

from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
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
TIMEOUT = 180  # NOT OK, ModbusRtuFramer and ModbusAsciiFramer have a hanger.


def to_be_solved(test_type, test_comm, test_framer):
    """Solve problems."""
    if test_framer == ModbusAsciiFramer:
        return True
    if test_type == "extended" and test_framer is not ModbusSocketFramer:
        return True
    if test_comm in ("udp", "serial"):  # pylint: disable=use-set-for-membership
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
        ("tcp", ModbusAsciiFramer),
        # Need a certificate: ("tls", ModbusTlsFramer),
        ("udp", ModbusSocketFramer),
        ("udp", ModbusRtuFramer),
        ("udp", ModbusAsciiFramer),
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

    loop = asyncio.get_event_loop()
    server = None
    server_id = None
    client = None
    not_ok_exc = None
    try:
        if test_server:
            server = server_sync(args=args)
            server_id = loop.run_in_executor(None, server.serve_forever)
        else:
            server = await server_async(args=args)
            server_id = asyncio.ensure_future(server.serve_forever())
        await asyncio.sleep(0.1)

        if test_client:
            client = client_setup_sync(args=args)
            await asyncio.wait_for(loop.run_in_executor(None, client_sync, client, method_client[test_type][0]), TIMEOUT)
        else:
            client = client_setup_async(args=args)
            await asyncio.wait_for(client_async(client, modbus_calls=method_client[test_type][1]), TIMEOUT)
    except Exception as exc:  # pylint: disable=broad-except # noqa: E722
        not_ok_exc = f"Server/Client raised exception <<{exc}>>"

    if test_server and server:
        server.shutdown()
    if server_id:
        while not server_id.done():
            server_id.cancel()
            await asyncio.sleep(0.1)
        assert server_id.cancelled()
    if client:
        if test_client:
            client.close()
        else:
            await client.aClose()
    if not_ok_exc:
        pytest.fail(not_ok_exc)


if __name__ == "__main__":
    asyncio.run(test_client_server("basic", True, False, "udp", ModbusSocketFramer))
