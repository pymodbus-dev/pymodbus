"""Test transport."""
import asyncio
import os
import time
from tempfile import gettempdir

import pytest

from pymodbus.framer import ModbusFramer, ModbusSocketFramer
from pymodbus.transport.transport import BaseTransport


class TestCommTransport:
    """Test for the transport module."""

    cwd = None

    @classmethod
    def setup_CWD(cls):
        """Get path to certificates."""
        cls.cwd = os.getcwd().split("/")[-1]
        if cls.cwd == "transport":
            cls.cwd = "../../"
        elif cls.cwd == "test":
            cls.cwd = "../"
        else:
            cls.cwd = ""
        cls.cwd = cls.cwd + "examples/certificates/pymodbus."

    class dummy_transport(BaseTransport):
        """Transport class for test."""

        def cb_connection_made(self):
            """Handle callback."""

        def cb_connection_lost(self, _exc):
            """Handle callback."""

        def cb_handle_data(self, _data):
            """Handle callback."""
            return 0

        def __init__(self, framer: ModbusFramer, comm_name="test comm"):
            """Initialize."""
            super().__init__(
                comm_name,
                [2500, 9000],
                2000,
                framer,
                self.cb_connection_made,
                self.cb_connection_lost,
                self.cb_handle_data,
            )

    @pytest.mark.skipif(
        pytest.IS_WINDOWS, reason="Windows do not support unix sockets."
    )
    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connect_unix(self):
        """Test connect_unix()."""
        client = self.dummy_transport(ModbusSocketFramer)
        domain_socket = "/domain_unix"
        client.setup_unix(False, domain_socket)
        start = time.time()
        assert await client.transport_connect() == (None, None)
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * 1.2

        client = self.dummy_transport(ModbusSocketFramer)
        domain_socket = gettempdir() + "/domain_unix"
        client.setup_unix(False, domain_socket)
        start = time.time()
        assert await client.transport_connect() == (None, None)
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * 1.2

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connect_tcp(self):
        """Test connect_tcp()."""
        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_tcp(False, "142.250.200.78", 502)
        start = time.time()
        assert await client.transport_connect() == (None, None)
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * 1.2

        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_tcp(False, "localhost", 5001)
        start = time.time()
        assert await client.transport_connect() == (None, None)
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * 1.2

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connect_tls(self):
        """Test connect_tls()."""
        self.setup_CWD()
        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_tls(
            False,
            "142.250.200.78",
            502,
            None,
            self.cwd + "crt",
            self.cwd + "key",
            None,
            "localhost",
        )
        start = time.time()
        assert await client.transport_connect() == (None, None)
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * 1.2

        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_tls(
            False,
            "127.0.0.1",
            5001,
            None,
            self.cwd + "crt",
            self.cwd + "key",
            None,
            "localhost",
        )
        start = time.time()
        assert await client.transport_connect() == (None, None)
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * 1.2

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connect_serial(self):
        """Test connect_serial()."""
        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_serial(
            False,
            "no_port",
            9600,
            8,
            "E",
            2,
        )
        start = time.time()
        assert await client.transport_connect() == (None, None)
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * 1.2

        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_serial(
            False,
            "unix:/localhost:5001",
            9600,
            8,
            "E",
            2,
        )
        start = time.time()
        assert await client.transport_connect() == (None, None)
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * 1.2

    @pytest.mark.skipif(
        pytest.IS_WINDOWS, reason="Windows do not support unix sockets."
    )
    @pytest.mark.xdist_group(name="server_serialize")
    async def test_listen_unix(self):
        """Test listen_unix()."""
        server = self.dummy_transport(ModbusSocketFramer)
        domain_socket = "/test_unix_"
        server.setup_unix(True, domain_socket)
        assert not await server.transport_listen()
        assert not server.transport

        server = self.dummy_transport(ModbusSocketFramer)
        domain_socket = gettempdir() + "/test_unix_" + str(time.time())
        server.setup_unix(True, domain_socket)
        assert await server.transport_listen()
        assert server.transport
        server.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_listen_tcp(self):
        """Test listen_tcp()."""
        server = self.dummy_transport(ModbusSocketFramer)
        server.setup_tcp(True, "10.0.0.1", 5101)
        assert not await server.transport_listen()
        assert not server.transport

        server = self.dummy_transport(ModbusSocketFramer)
        server.setup_tcp(True, "localhost", 5101)
        assert await server.transport_listen()
        assert server.transport
        server.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_listen_tls(self):
        """Test listen_tls()."""
        self.setup_CWD()
        server = self.dummy_transport(ModbusSocketFramer)
        server.setup_tls(
            True,
            "10.0.0.1",
            5101,
            None,
            self.cwd + "crt",
            self.cwd + "key",
            None,
            "localhost",
        )
        assert not await server.transport_listen()
        assert not server.transport

        server = self.dummy_transport(ModbusSocketFramer)
        server.setup_tls(
            True,
            "127.0.0.1",
            5101,
            None,
            self.cwd + "crt",
            self.cwd + "key",
            None,
            "localhost",
        )
        assert await server.transport_listen()
        assert server.transport
        server.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_listen_udp(self):
        """Test listen_udp()."""
        server = self.dummy_transport(ModbusSocketFramer)
        server.setup_udp(True, "10.0.0.1", 5101)
        assert not await server.transport_listen()
        assert not server.transport

        server = self.dummy_transport(ModbusSocketFramer)
        server.setup_udp(True, "localhost", 5101)
        assert await server.transport_listen()
        assert server.transport
        server.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_listen_serial(self):
        """Test listen_serial()."""
        server = self.dummy_transport(ModbusSocketFramer)
        server.setup_serial(
            True,
            "no port",
            9600,
            8,
            "E",
            2,
        )
        assert not await server.transport_listen()
        assert not server.transport

        # there are no positive test, since there are no standard tty port

    @pytest.mark.skipif(
        pytest.IS_WINDOWS, reason="Windows do not support unix sockets."
    )
    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connected_unix(self):
        """Test listen/connect unix()."""
        server_protocol = self.dummy_transport(ModbusSocketFramer)
        domain_socket = gettempdir() + "/test_unix_" + str(time.time())
        server_protocol.setup_unix(True, domain_socket)
        await server_protocol.transport_listen()

        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_unix(False, domain_socket)
        assert await client.transport_connect() != (None, None)
        client.close()
        server_protocol.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connected_tcp(self):
        """Test listen/connect tcp()."""
        server_protocol = self.dummy_transport(ModbusSocketFramer)
        server_protocol.setup_tcp(True, "localhost", 5101)
        assert await server_protocol.transport_listen()

        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_tcp(False, "localhost", 5101)
        assert await client.transport_connect() != (None, None)
        client.close()
        server_protocol.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connected_tls(self):
        """Test listen/connect tls()."""
        self.setup_CWD()
        server_protocol = self.dummy_transport(ModbusSocketFramer)
        server_protocol.setup_tls(
            True,
            "127.0.0.1",
            5102,
            None,
            self.cwd + "crt",
            self.cwd + "key",
            None,
            "localhost",
        )
        assert await server_protocol.transport_listen()

        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_tls(
            False,
            "127.0.0.1",
            5102,
            None,
            self.cwd + "crt",
            self.cwd + "key",
            None,
            "localhost",
        )
        assert await client.transport_connect() != (None, None)
        client.close()
        server_protocol.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connected_udp(self):
        """Test listen/connect udp()."""
        server_protocol = self.dummy_transport(ModbusSocketFramer)
        server_protocol.setup_udp(True, "localhost", 5101)
        transport = await server_protocol.transport_listen()
        assert transport

        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_udp(False, "localhost", 5101)
        assert await client.transport_connect() != (None, None)
        client.close()
        server_protocol.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connected_serial(self):
        """Test listen/connect serial()."""
        server_protocol = self.dummy_transport(ModbusSocketFramer)
        server_protocol.setup_tcp(True, "localhost", 5101)
        assert await server_protocol.transport_listen()

        client = self.dummy_transport(ModbusSocketFramer)
        client.setup_serial(
            False,
            "unix:localhost:5001",
            9600,
            8,
            "E",
            2,
        )
        assert await client.transport_connect() == (None, None)
        client.close()
        server_protocol.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_connect_reconnect(self):
        """Test connect() reconnecting."""
        server = self.dummy_transport(ModbusSocketFramer, comm_name="server mode")
        server.setup_tcp(True, "localhost", 5101)
        await server.transport_listen()
        assert server.transport

        client = self.dummy_transport(ModbusSocketFramer, comm_name="client mode")
        client.setup_tcp(False, "localhost", 5101)
        assert await client.transport_connect() != (None, None)
        server.close()
        count = 100
        while client.transport and count:
            await asyncio.sleep(0.1)
            count -= 1
        assert not client.transport
        assert client.reconnect_timer
        assert client.reconnect_delay_current == 2 * client.comm_params.reconnect_delay
        await asyncio.sleep(client.reconnect_delay_current * 1.2)
        assert client.transport
        assert client.reconnect_timer
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay
        client.close()
        server.close()
