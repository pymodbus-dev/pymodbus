"""Test example server/client async

This is a thorough test of the clientexamples.

"""
import asyncio
import logging

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
from examples.server_payload import setup_payload_server
from pymodbus import pymodbus_apply_logging_config
from pymodbus.server import ServerAsyncStop


_logger = logging.getLogger()
_logger.setLevel("DEBUG")
pymodbus_apply_logging_config("DEBUG")


class TestExamples:
    """Test examples."""

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

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    async def test_client_calls(self, mock_server):
        """Test client_calls."""
        cmdline = mock_server
        test_client = setup_async_client(cmdline=cmdline)
        await run_async_client(test_client, modbus_calls=run_async_calls)

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
        ],
    )
    def test_custom_msg(self, use_port, mock_server):
        """Test client with custom message."""
        _cmdline = mock_server
        run_custom_client("localhost", use_port)

    @pytest.mark.xdist_group(name="server_serialize")
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
        ],
    )
    async def test_payload(self, mock_cmdline):
        """Test server/client with payload."""
        run_args = setup_payload_server(cmdline=mock_cmdline)
        task = asyncio.create_task(run_async_server(run_args))
        await asyncio.sleep(0.1)
        testclient = setup_async_client(cmdline=mock_cmdline)
        await run_async_client(testclient, modbus_calls=run_payload_calls)
        await asyncio.sleep(0.1)
        await ServerAsyncStop()
        await asyncio.sleep(0.1)
        task.cancel()
        await task

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_datastore_simulator(self, use_port):
        """Test server simulator."""
        cmdargs = ["--log", "debug", "--port", str(use_port)]
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

    # modbus_forwarder.py
    # server_callback.py
    # server_updating.py

    # simple_async_client.py
    # simple_sync_client.py
