"""Test example server/client async

This is a thorough test of the
- client_async.py
- server_async.py
examples.

These are basis for most examples and thus tested separately
"""
import asyncio

import pytest

from examples.client_async import run_a_few_calls, run_async_client, setup_async_client


BASE_PORT = 6200


class TestClientServerAsyncExamples:
    """Test Client server async examples."""

    USE_CASES = [
        ("tcp", "socket", BASE_PORT + 1),
        ("tcp", "rtu", BASE_PORT + 2),
        ("tls", "tls", BASE_PORT + 3),
        ("udp", "socket", BASE_PORT + 4),
        ("udp", "rtu", BASE_PORT + 5),
        ("serial", "rtu", BASE_PORT + 6),
        # awaiting fix: ("serial", "ascii", BASE_PORT + 7),
        # awaiting fix: ("serial", "binary", BASE_PORT + 8),
    ]

    @pytest.mark.parametrize("port_offset", [0])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        USE_CASES,
    )
    async def test_combinations(self, mock_server, mock_clc):
        """Run async client and server."""
        assert mock_server
        test_client = setup_async_client(cmdline=mock_clc)
        await run_async_client(test_client, modbus_calls=run_a_few_calls)

    @pytest.mark.parametrize("port_offset", [10])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        USE_CASES,
    )
    async def test_server_no_client(self, mock_server):
        """Run async server without client."""
        assert mock_server

    @pytest.mark.parametrize("port_offset", [20])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        USE_CASES,
    )
    async def test_server_client_twice(self, mock_server, use_comm, mock_clc):
        """Run async server without client."""
        assert mock_server
        if use_comm == "serial":
            return
        test_client = setup_async_client(cmdline=mock_clc)
        await run_async_client(test_client, modbus_calls=run_a_few_calls)
        await asyncio.sleep(0.5)
        await run_async_client(test_client, modbus_calls=run_a_few_calls)

    @pytest.mark.parametrize("port_offset", [30])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        USE_CASES,
    )
    async def test_client_no_server(self, mock_clc):
        """Run async client without server."""
        test_client = setup_async_client(cmdline=mock_clc)
        with pytest.raises((AssertionError, asyncio.TimeoutError)):
            await run_async_client(test_client, modbus_calls=run_a_few_calls)
