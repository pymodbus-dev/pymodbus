"""Test example server/client sync.

This is a thorough test of the
- client_sync.py
- server_sync.py
examples.

These are basis for most examples and thus tested separately
"""
import os
from threading import Thread
from time import sleep

import pytest

from examples.client_sync import (
    main,
    run_a_few_calls,
    run_sync_client,
    setup_sync_client,
)
from examples.server_async import setup_server
from examples.server_sync import run_sync_server
from pymodbus.exceptions import ConnectionException
from pymodbus.server import ServerStop


if os.name == "nt":
    SLEEPING = 5
else:
    SLEEPING = 1


@pytest.mark.parametrize("use_host", ["localhost"])
@pytest.mark.parametrize(
    ("use_comm", "use_framer"),
    [
        ("tcp", "socket"),
        ("tcp", "rtu"),
        # awaiting fix: ("tls", "tls"),
        ("udp", "socket"),
        ("udp", "rtu"),
        ("serial", "rtu"),
    ],
)
class TestClientServerSyncExamples:
    """Test Client server async combinations."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port."""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

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
        sleep(SLEEPING)
        main(cmdline=mock_clc)
        ServerStop()

    def test_server_no_client(self, mock_cls):
        """Run async server without client."""
        server_args = setup_server(cmdline=mock_cls)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(SLEEPING)
        ServerStop()

    def test_server_client_twice(self, mock_cls, mock_clc, use_comm):
        """Run async server without client."""
        if use_comm == "serial":
            # cannot open the usb port multiple times
            return
        server_args = setup_server(cmdline=mock_cls)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(SLEEPING)
        test_client = setup_sync_client(cmdline=mock_clc)
        run_sync_client(test_client, modbus_calls=run_a_few_calls)
        sleep(SLEEPING)
        run_sync_client(test_client, modbus_calls=run_a_few_calls)
        ServerStop()

    def test_client_no_server(self, mock_clc):
        """Run async client without server."""
        if mock_clc[1] == "udp":
            # udp is connectionless, so it it not possible to detect a proper connection
            # instead it fails on first message exchange
            return
        test_client = setup_sync_client(cmdline=mock_clc)
        with pytest.raises((AssertionError, ConnectionException)):
            run_sync_client(test_client, modbus_calls=run_a_few_calls)
