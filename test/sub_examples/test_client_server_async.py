"""Test example server/client async

This is a thorough test of the
- client_async.py
- server_async.py
examples.

These are basis for most examples and thus tested separately
"""
import asyncio
import logging

import pytest

from examples.client_async import run_a_few_calls, run_async_client, setup_async_client
from pymodbus import pymodbus_apply_logging_config


_logger = logging.getLogger()
_logger.setLevel("DEBUG")
pymodbus_apply_logging_config("DEBUG")


class TestClientServerAsyncExamples:
    """Test Client server async examples."""

    USE_CASES = [
        ("tcp", "socket"),
        ("tcp", "rtu"),
        ("tls", "tls"),
        ("udp", "socket"),
        ("udp", "rtu"),
        ("serial", "rtu"),
        # awaiting fix: ("serial", "ascii"),
        # awaiting fix: ("serial", "binary"),
    ]

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    async def test_combinations(self, mock_server):
        """Run async client and server."""
        cmdline = mock_server
        test_client = setup_async_client(cmdline=cmdline)
        await run_async_client(test_client, modbus_calls=run_a_few_calls)

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    async def test_server_no_client(self, mock_server):
        """Run async server without client."""
        assert mock_server

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    async def test_server_client_twice(self, mock_server):
        """Run async server without client."""
        cmdline = mock_server
        test_client = setup_async_client(cmdline=cmdline)
        await run_async_client(test_client, modbus_calls=run_a_few_calls)
        await asyncio.sleep(0.5)
        await run_async_client(test_client, modbus_calls=run_a_few_calls)

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    async def test_client_no_server(self, mock_cmdline):
        """Run async client without server."""
        test_client = setup_async_client(cmdline=mock_cmdline)
        with pytest.raises((AssertionError, asyncio.TimeoutError)):
            await run_async_client(test_client, modbus_calls=run_a_few_calls)
