"""Test example server/client async

This is a thorough test of the clientexamples.

"""
import asyncio
from threading import Thread
from time import sleep
from unittest import mock

import pytest

from examples.client_async import run_a_few_calls, run_async_client, setup_async_client
from examples.client_async_calls import async_template_call
from examples.client_async_calls import main as main_client_async_calls
from examples.client_calls import main as main_client_calls
from examples.client_calls import template_call
from examples.client_custom_msg import main as main_custom_client
from examples.client_payload import main as main_payload_calls
from examples.datastore_simulator import main as main_datastore_simulator
from examples.message_generator import generate_messages
from examples.message_parser import main as main_parse_messages
from examples.server_async import setup_server
from examples.server_callback import run_callback_server
from examples.server_payload import main as main_payload_server
from examples.server_sync import run_sync_server
from examples.server_updating import main as main_updating_server
from examples.simple_async_client import run_async_simple_client
from examples.simple_sync_client import run_sync_simple_client
from examples.simulator import run_simulator
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse
from pymodbus.server import ServerAsyncStop, ServerStop
from pymodbus.transport import NullModem


class TestExamples:
    """Test examples."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_my_port(base_ports):
        """Return next port"""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    def teardown(self):
        """Run class teardown"""
        assert not NullModem.is_dirty()

    USE_CASES = [
        ("tcp", "socket"),
        ("tcp", "rtu"),
        ("tls", "tls"),
        ("udp", "socket"),
        ("udp", "rtu"),
        ("serial", "rtu"),
        # awaiting fix: ("serial", "ascii", BASE_PORT + 7),
        # awaiting fix: ("serial", "binary", BASE_PORT + 8),
    ]

    @pytest.mark.parametrize("framer", ["socket", "rtu", "ascii", "binary"])
    def test_message_generator(self, framer):
        """Test all message generator."""
        generate_messages(cmdline=["--framer", framer])

    def test_message_parser(self):
        """Test message parser."""
        main_parse_messages(["--framer", "socket", "-m", "000100000006010100200001"])
        main_parse_messages(["--framer", "socket", "-m", "00010000000401010101"])

    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        USE_CASES,
    )
    async def test_client_async_calls(self, mock_server):
        """Test client_async_calls."""
        await main_client_async_calls(cmdline=mock_server)

    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
        ],
    )
    async def test_client_async_calls_errors(self, mock_server):
        """Test client_async_calls."""
        client = setup_async_client(cmdline=mock_server)
        client.read_coils = mock.AsyncMock(side_effect=ModbusException("test"))
        with pytest.raises(ModbusException):
            await run_async_client(client, modbus_calls=async_template_call)
        client.close()
        client.read_coils = mock.AsyncMock(return_value=ExceptionResponse(0x05, 0x10))
        with pytest.raises(ModbusException):
            await run_async_client(client, modbus_calls=async_template_call)
        client.close()

    @pytest.mark.parametrize("use_host", ["localhost"])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
            ("tcp", "rtu"),
            # awaiting fix: ("tls", "tls", BASE_PORT + 3),
            ("udp", "socket"),
            ("udp", "rtu"),
            ("serial", "rtu"),
            # awaiting fix: ("serial", "ascii", BASE_PORT + 7),
            # awaiting fix: ("serial", "binary", BASE_PORT + 8),
        ],
    )
    def test_client_calls(self, mock_clc, mock_cls):
        """Test client_calls."""
        server_args = setup_server(cmdline=mock_cls)
        thread = Thread(target=run_sync_server, args=(server_args,))
        thread.daemon = True
        thread.start()
        sleep(1)
        main_client_calls(cmdline=mock_clc)
        ServerStop()

    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
        ],
    )
    async def test_client_calls_errors(self, mock_server):
        """Test client_calls."""
        client = setup_async_client(cmdline=mock_server)
        client.read_coils = mock.Mock(side_effect=ModbusException("test"))
        with pytest.raises(ModbusException):
            await run_async_client(client, modbus_calls=template_call)
        client.close()
        client.read_coils = mock.Mock(return_value=ExceptionResponse(0x05, 0x10))
        with pytest.raises(ModbusException):
            await run_async_client(client, modbus_calls=template_call)
        client.close()

    @pytest.mark.parametrize("use_host", ["localhost"])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
        ],
    )
    async def test_custom_msg(self, mock_server, use_port, use_host):
        """Test client with custom message."""
        assert mock_server
        await main_custom_client(port=use_port, host=use_host)

    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
        ],
    )
    async def test_payload(self, mock_clc, mock_cls):
        """Test server/client with payload."""
        task = asyncio.create_task(main_payload_server(cmdline=mock_cls))
        await asyncio.sleep(0.1)
        await main_payload_calls(cmdline=mock_clc)
        await asyncio.sleep(0.1)
        await ServerAsyncStop()
        await asyncio.sleep(0.1)
        task.cancel()
        await task

    async def test_datastore_simulator(self, use_port):
        """Test server simulator."""
        cmdargs = ["--port", str(use_port)]
        task = asyncio.create_task(
            main_datastore_simulator(cmdline=["--port", str(use_port)])
        )
        await asyncio.sleep(0.1)
        cmdargs.extend(["--host", "localhost"])
        testclient = setup_async_client(cmdline=cmdargs)
        await run_async_client(testclient, modbus_calls=run_a_few_calls)
        await asyncio.sleep(0.1)
        await ServerAsyncStop()
        await asyncio.sleep(0.1)
        task.cancel()
        await task

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

    async def test_updating_server(self, use_port):
        """Test server simulator."""
        cmdargs = ["--port", str(use_port)]
        task = asyncio.create_task(main_updating_server(cmdline=cmdargs))
        await asyncio.sleep(0.1)
        client = setup_async_client(cmdline=cmdargs)
        await run_async_client(client, modbus_calls=run_a_few_calls)
        await asyncio.sleep(0.1)
        await ServerAsyncStop()
        await asyncio.sleep(0.1)
        task.cancel()
        await task

    @pytest.mark.parametrize("use_host", ["localhost"])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
            # awaiting fix ("tls", "tls", BASE_PORT + 47),
            ("udp", "socket"),
            ("serial", "rtu"),
        ],
    )
    async def test_async_simple_client(self, use_comm, use_port, mock_server, use_host):
        """Run simple async client."""
        _cmdline = mock_server
        if use_comm == "serial":
            use_port = f"socket://{use_host}:{use_port}"
        await run_async_simple_client(use_comm, use_host, use_port)

    @pytest.mark.parametrize("use_host", ["localhost"])
    @pytest.mark.parametrize(
        ("use_comm", "use_framer"),
        [
            ("tcp", "socket"),
            # awaiting fix ("tls", "tls", BASE_PORT + 47),
            ("udp", "socket"),
            ("serial", "rtu"),
        ],
    )
    async def test_sync_simple_client(self, use_comm, use_host, use_port, mock_server):
        """Run simple async client."""
        _cmdline = mock_server
        if use_comm == "serial":
            use_port = f"socket://{use_host}:{use_port}"
        run_sync_simple_client(use_comm, use_host, use_port)

    async def test_simulator(self):
        """Run simulator server/client."""
        await run_simulator()

    async def test_modbus_forwarder(self):
        """Test modbus forwarder."""
        print("waiting for fix")
