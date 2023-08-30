"""Test example server/client async

This is a thorough test of the
- client_async.py
- server_async.py
examples.

These are basis for most examples and thus tested separately
"""
import asyncio
from unittest import mock

import pytest

from examples.client_async import (
    main,
    run_a_few_calls,
    run_async_client,
    setup_async_client,
)
from pymodbus.exceptions import ModbusIOException


@pytest.mark.parametrize(
    ("use_comm", "use_framer"),
    [
        ("tcp", "socket"),
        ("tcp", "rtu"),
        ("tls", "tls"),
        ("udp", "socket"),
        ("udp", "rtu"),
        ("serial", "rtu"),
    ],
)
class TestClientServerAsyncExamples:
    """Test Client server async examples."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port"""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    async def test_combinations(self, mock_server, mock_clc):
        """Run async client and server."""
        assert mock_server
        await main(cmdline=mock_clc)

    async def test_client_exception(self, mock_server, mock_clc):
        """Run async client and server."""
        assert mock_server
        test_client = setup_async_client(cmdline=mock_clc)
        test_client.read_holding_registers = mock.AsyncMock(
            side_effect=ModbusIOException("test")
        )
        await run_async_client(test_client, modbus_calls=run_a_few_calls)

    async def test_server_no_client(self, mock_server):
        """Run async server without client."""
        assert mock_server

    async def test_server_client_twice(self, mock_server, use_comm, mock_clc):
        """Run async server without client."""
        assert mock_server
        if use_comm == "serial":
            # Serial do not allow mmulti point.
            return
        test_client = setup_async_client(cmdline=mock_clc)
        await run_async_client(test_client, modbus_calls=run_a_few_calls)
        await asyncio.sleep(0.5)
        await run_async_client(test_client, modbus_calls=run_a_few_calls)

    async def test_client_no_server(self, mock_clc):
        """Run async client without server."""
        test_client = setup_async_client(cmdline=mock_clc)
        with pytest.raises((AssertionError, asyncio.TimeoutError)):
            await run_async_client(test_client, modbus_calls=run_a_few_calls)
