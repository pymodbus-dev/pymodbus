"""Test example server/client async

This is a thorough test of the clientexamples.

"""
import asyncio

import pytest

from examples.build_bcd_payload import BcdPayloadBuilder, BcdPayloadDecoder
from examples.client_async import run_a_few_calls, run_async_client, setup_async_client
from examples.client_calls import run_async_calls
from examples.client_custom_msg import run_custom_client
from examples.client_payload import run_payload_calls
from examples.datastore_simulator import run_server_simulator, setup_simulator
from examples.message_generator import generate_messages
from examples.message_parser import parse_messages
from examples.server_async import run_async_server
from examples.server_callback import run_callback_server
from examples.server_payload import setup_payload_server
from examples.server_updating import run_updating_server, setup_updating_server
from examples.simple_async_client import run_async_client as run_simple_async_client
from examples.simple_sync_client import run_sync_client as run_simple_sync_client
from pymodbus.server import ServerAsyncStop


BASE_PORT = 6400


class TestExamples:
    """Test examples."""

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

    def test_build_bcd_payload(self):
        """Test build bcd payload."""
        builder = BcdPayloadBuilder()
        decoder = BcdPayloadDecoder(builder)
        assert str(decoder)

    @pytest.mark.parametrize("framer", ["socket", "rtu", "ascii", "binary"])
    def test_message_generator(self, framer):
        """Test all message generator."""
        generate_messages(cmdline=["--framer", framer])

    def test_message_parser(self):
        """Test message parser."""
        parse_messages(["--framer", "socket", "-m", "000100000006010100200001"])
        parse_messages(["--framer", "socket", "-m", "00010000000401010101"])

    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        USE_CASES,
    )
    async def test_client_calls(self, mock_server):
        """Test client_calls."""
        cmdline = mock_server
        test_client = setup_async_client(cmdline=cmdline)
        await run_async_client(test_client, modbus_calls=run_async_calls)

    @pytest.mark.parametrize("use_host", ["localhost"])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        [
            ("tcp", "socket", BASE_PORT + 41),
        ],
    )
    def xtest_custom_msg(self, use_port, mock_server):
        """Test client with custom message."""
        _cmdline = mock_server
        run_custom_client("localhost", use_port)

    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        [
            ("tcp", "socket", BASE_PORT + 42),
        ],
    )
    async def test_payload(self, mock_clc, mock_cls):
        """Test server/client with payload."""
        run_args = setup_payload_server(cmdline=mock_cls)
        task = asyncio.create_task(run_async_server(run_args))
        await asyncio.sleep(0.1)
        testclient = setup_async_client(cmdline=mock_clc)
        await run_async_client(testclient, modbus_calls=run_payload_calls)
        await asyncio.sleep(0.1)
        await ServerAsyncStop()
        await asyncio.sleep(0.1)
        task.cancel()
        await task

    @pytest.mark.parametrize("use_port", [BASE_PORT + 43])
    async def test_datastore_simulator(self, use_port):
        """Test server simulator."""
        cmdargs = ["--port", str(use_port)]
        run_args = setup_simulator(cmdline=cmdargs)
        task = asyncio.create_task(run_server_simulator(run_args))
        await asyncio.sleep(0.1)
        cmdargs.extend(["--host", "localhost"])
        testclient = setup_async_client(cmdline=cmdargs)
        await run_async_client(testclient, modbus_calls=run_a_few_calls)
        await asyncio.sleep(0.1)
        await ServerAsyncStop()
        await asyncio.sleep(0.1)
        task.cancel()
        await task

    @pytest.mark.parametrize("use_port", [BASE_PORT + 44])
    async def test_server_callback(self, use_port):
        """Test server/client with payload."""
        cmdargs = ["--port", str(use_port)]
        task = asyncio.create_task(run_callback_server(cmdline=cmdargs))
        await asyncio.sleep(0.1)
        testclient = setup_async_client(cmdline=cmdargs)
        await run_async_client(testclient, modbus_calls=run_a_few_calls)
        await asyncio.sleep(0.1)
        await ServerAsyncStop()
        await asyncio.sleep(0.1)
        task.cancel()
        await task

    @pytest.mark.parametrize("use_port", [BASE_PORT + 45])
    async def test_updating_server(self, use_port):
        """Test server simulator."""
        cmdargs = ["--port", str(use_port)]
        run_args = setup_updating_server(cmdline=cmdargs)
        task = asyncio.create_task(run_updating_server(run_args))
        await asyncio.sleep(0.1)
        testclient = setup_async_client(cmdline=cmdargs)
        await run_async_client(testclient, modbus_calls=run_a_few_calls)
        await asyncio.sleep(0.1)
        await ServerAsyncStop()
        await asyncio.sleep(0.1)
        task.cancel()
        await task

    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        [
            ("tcp", "socket", BASE_PORT + 46),
        ],
    )
    async def test_simple_async_client(self, use_port, mock_server):
        """Run simple async client."""
        _cmdline = mock_server
        await run_simple_async_client("127.0.0.1", str(use_port))

    @pytest.mark.parametrize(
        ("use_comm", "use_framer", "use_port"),
        [
            ("tcp", "socket", BASE_PORT + 47),
        ],
    )
    async def test_simple_sync_client(self, use_port, mock_server):
        """Run simple async client."""
        _cmdline = mock_server
        run_simple_sync_client("127.0.0.1", str(use_port))

    async def test_modbus_forwarder(self):
        """Test modbus forwarder."""
        print("waiting for fix")
