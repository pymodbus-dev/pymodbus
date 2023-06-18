"""Test example server/client sync

This is a thorough test of the
- client_sync.py
- server_sync.py
examples.

These are basis for most examples and thus tested separately
"""
from threading import Thread
from time import sleep

import pytest

from examples.client_sync import run_a_few_calls, run_sync_client, setup_sync_client
from examples.server_async import setup_server
from examples.server_sync import run_sync_server
from pymodbus.exceptions import ConnectionException
from pymodbus.server import ServerStop


class TestClientServerSyncExamples:
    """Test Client server async combinations."""

    USE_CASES = [
        ("tcp", "socket"),
        ("tcp", "rtu"),
        # awaiting fix: ("tls", "tls"),
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
    def test_combinations(
        self,
        mock_cmdline,
    ):
        """Run sync client and server."""
        server_args = setup_server(cmdline=mock_cmdline)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(1)
        test_client = setup_sync_client(cmdline=mock_cmdline)
        run_sync_client(test_client, modbus_calls=run_a_few_calls)
        ServerStop()

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    def test_server_no_client(self, mock_cmdline):
        """Run async server without client."""
        server_args = setup_server(cmdline=mock_cmdline)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(1)
        ServerStop()

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    def test_server_client_twice(self, mock_cmdline):
        """Run async server without client."""
        server_args = setup_server(cmdline=mock_cmdline)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(1)
        test_client = setup_sync_client(cmdline=mock_cmdline)
        run_sync_client(test_client, modbus_calls=run_a_few_calls)
        sleep(0.5)
        run_sync_client(test_client, modbus_calls=run_a_few_calls)
        ServerStop()

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    def test_client_no_server(self, mock_cmdline):
        """Run async client without server."""
        if mock_cmdline[1] == "udp":
            # udp is connectionless, so it it not possible to detect a proper connection
            # instead it fails on first message exchange
            return
        test_client = setup_sync_client(cmdline=mock_cmdline)
        with pytest.raises((AssertionError, ConnectionException)):
            run_sync_client(test_client, modbus_calls=run_a_few_calls)
