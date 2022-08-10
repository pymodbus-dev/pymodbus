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


@dataclass
class Commandline:
    """Simulate commandline parameters."""

    comm = None
    framer = None
    port = None

    store = "sequential"
    slaves = None
    modbus_calls = None
    prepare = True


@pytest.mark.parametrize(
    "test_type",
    [
        "connect",
        "basic",
        # "extended",
    ]
)
@pytest.mark.parametrize(
    "test_server, test_client",
    [
        (True, True),
        # NOT OK (True, False),
        # NOT OK (False, True),
        # NOT OK (False, False),
    ]
)
@pytest.mark.parametrize(
    "test_comm, test_framer",
    [
        ("tcp", ModbusSocketFramer),
        ("tcp", ModbusRtuFramer),
        ("tcp", ModbusAsciiFramer),
        ("no tcp", ModbusBinaryFramer),  # NOT OK
        ("no tls", ModbusTlsFramer),  # NOT OK
        ("no udp", ModbusSocketFramer),  # NOT OK
        ("no udp", ModbusRtuFramer),  # NOT OK
        ("no udp", ModbusAsciiFramer),  # NOT OK
        ("no udp", ModbusBinaryFramer),  # NOT OK
        ("no serial", ModbusRtuFramer),  # NOT OK
        ("no serial", ModbusAsciiFramer),  # NOT OK
        ("no serial", ModbusBinaryFramer),  # NOT OK
    ]
)
async def test_client_server(test_type, test_server, test_client, test_comm, test_framer):
    """Test client/server examples."""

    if test_comm[:2] == "no":
        return
    args = Commandline()
    args.comm = test_comm
    args.framer = test_framer
    args.port = "/dev/ttyp0" if args.comm == "serial" else "5020"

    _logger.setLevel("DEBUG")

    loop = asyncio.get_event_loop()
    if test_server:
        server = server_sync(args=args)
        server_id = loop.run_in_executor(None, server.serve_forever)
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
    server_id.cancel()
    assert server_id.cancelled()


if __name__ == "__main__":
    asyncio.run(test_client_server("connect", True, True, "tcp", ModbusSocketFramer))
