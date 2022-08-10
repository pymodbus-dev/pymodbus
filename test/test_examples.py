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
    ModbusTlsFramer,
)

from examples.server_sync import run_server as server_sync
from examples.server_async import run_server as server_async
from examples.client_sync import run_client as client_sync
from examples.client_async import run_client as client_async
from examples.client_sync_basic_calls import demonstrate_calls as demo_sync_basic
from examples.client_sync_extended_calls import demonstrate_calls as demo_sync_extended
from examples.client_async_basic_calls import demonstrate_calls as demo_async_basic
from examples.client_async_extended_calls import demonstrate_calls as demo_async_extended


_logger = logging.getLogger()

EXAMPLE_PATH = "../examples"
PYTHON = "python3"


def to_be_solved(test_type, test_framer, test_server, test_comm, test_client):
    """Solve problems."""
    if test_type == "extended" and test_framer is not ModbusSocketFramer:
        return True
    if not test_server:
        return True
    if test_comm in ("tls", "udp", "serial"):  # pylint: disable=use-set-for-membership
        return True
    if not test_client and (test_framer is not ModbusSocketFramer or test_comm != "tcp"):
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
        ("tls", ModbusTlsFramer),
        ("udp", ModbusSocketFramer),
        ("udp", ModbusRtuFramer),
        ("udp", ModbusAsciiFramer),
        ("serial", ModbusRtuFramer),
        ("serial", ModbusAsciiFramer),
        ("serial", ModbusBinaryFramer),
    ]
)
async def test_client_server(test_type, test_server, test_client, test_comm, test_framer):
    """Test client/server examples."""

    if to_be_solved(
        test_type,
        test_framer,
        test_server,
        test_comm,
        test_client,
    ):
        return

    args = Commandline()
    args.comm = test_comm
    args.framer = test_framer
    args.port = "/dev/ttyp0" if args.comm == "serial" else "5020"

    _logger.setLevel("DEBUG")

    def run_sync_server():
        """Catch exceptions."""
        try:
            server.serve_forever()
        except:  # pylint: disable=bare-except # noqa: E722
            server.shutdown()
            pytest.fail("Server raised an exception")

    loop = asyncio.get_event_loop()
    if test_server:
        server = server_sync(args=args)
        server_id = loop.run_in_executor(None, run_sync_server)
    else:
        server = server_async(args=args)
    await asyncio.sleep(0.1)

    method_client = {
        "connect": (None, None),
        "basic": (demo_sync_basic, demo_async_basic),
        "extended": (demo_sync_extended, demo_async_extended),
    }
    if test_client:
        client_sync(modbus_calls=method_client[test_type][0], args=args)
    else:
        await client_async(modbus_calls=method_client[test_type][1], args=args)
    server.shutdown()
    assert server.socket
    server_id.cancel()
    assert server_id.cancelled()


if __name__ == "__main__":
    asyncio.run(test_client_server("basic", True, False, "tcp", ModbusSocketFramer))
