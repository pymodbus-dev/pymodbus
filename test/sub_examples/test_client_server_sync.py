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


BASE_PORT = 6300


class TestClientServerSyncExamples:
    """Test Client server async combinations."""

    USE_CASES = [
        ("tcp", "socket", BASE_PORT + 1),
        ("tcp", "rtu", BASE_PORT + 2),
        # awaiting fix: ("tls", "tls", BASE_PORT + 3),
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
    def test_combinations(
        self,
        mock_clc,
        mock_cls,
    ):
        """Run sync client and server."""
        server_args = setup_server(cmdline=mock_cls)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(1)
        test_client = setup_sync_client(cmdline=mock_clc)
        run_sync_client(test_client, modbus_calls=run_a_few_calls)
        ServerStop()

    @pytest.mark.parametrize("port_offset", [10])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        USE_CASES,
    )
    def test_server_no_client(self, mock_cls):
        """Run async server without client."""
        server_args = setup_server(cmdline=mock_cls)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(1)
        ServerStop()

    @pytest.mark.parametrize("port_offset", [20])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        USE_CASES,
    )
    def test_server_client_twice(self, mock_cls, mock_clc, use_comm):
        """Run async server without client."""
        if use_comm == "serial":
            return
        server_args = setup_server(cmdline=mock_cls)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(1)
        test_client = setup_sync_client(cmdline=mock_clc)
        run_sync_client(test_client, modbus_calls=run_a_few_calls)
        sleep(0.5)
        run_sync_client(test_client, modbus_calls=run_a_few_calls)
        ServerStop()

    @pytest.mark.parametrize("port_offset", [30])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        USE_CASES,
    )
    def test_client_no_server(self, mock_clc):
        """Run async client without server."""
        if mock_clc[1] == "udp":
            # udp is connectionless, so it it not possible to detect a proper connection
            # instead it fails on first message exchange
            return
        test_client = setup_sync_client(cmdline=mock_clc)
        with pytest.raises((AssertionError, ConnectionException)):
            run_sync_client(test_client, modbus_calls=run_a_few_calls)
