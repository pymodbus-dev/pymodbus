"""Test transport."""
import asyncio
import time

import pytest

from pymodbus.transport.transport import CommType


BASE_PORT = 6100
FACTOR = 1.2 if not pytest.IS_WINDOWS else 2.2


class TestCommTransport:
    """Test for the transport module."""

    @pytest.mark.parametrize(
        ("use_comm_type", "use_port"),
        [
            (CommType.TCP, BASE_PORT + 1),
            (CommType.TLS, BASE_PORT + 2),
            # (CommType.UDP, BASE_PORT + 3), udp is connectionless.
            (CommType.SERIAL, BASE_PORT + 4),
        ],
    )
    async def test_connect(self, client):
        """Test connect()."""
        start = time.time()
        assert not await client.transport_connect()
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * FACTOR
        client.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_port"),
        [
            (CommType.TCP, BASE_PORT + 5),
            (CommType.TLS, BASE_PORT + 6),
            # (CommType.UDP, BASE_PORT + 7), udp is connectionless.
            (CommType.SERIAL, BASE_PORT + 8),
        ],
    )
    async def test_connect_not_ok(self, client):
        """Test connect()."""
        client.comm_params.host = "/illegal_host"
        start = time.time()
        assert not await client.transport_connect()
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * FACTOR
        client.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_port"),
        [
            (CommType.TCP, BASE_PORT + 9),
            (CommType.TLS, BASE_PORT + 10),
            (CommType.UDP, BASE_PORT + 11),
            # (CommType.SERIAL, BASE_PORT + 12), there are no standard tty port
        ],
    )
    async def test_listen(self, server):
        """Test listen()."""
        assert await server.transport_listen()
        assert server.transport
        server.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_port"),
        [
            (CommType.TCP, BASE_PORT + 13),
            (CommType.TLS, BASE_PORT + 14),
            (CommType.UDP, BASE_PORT + 15),
            (CommType.SERIAL, BASE_PORT + 16),
        ],
    )
    async def test_listen_not_ok(self, server):
        """Test listen()."""
        server.comm_params.host = "/illegal_host"
        assert not await server.transport_listen()
        assert not server.transport
        server.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_port"),
        [
            (CommType.TCP, BASE_PORT + 13),
            (CommType.TLS, BASE_PORT + 14),
            (CommType.UDP, BASE_PORT + 15),
            (CommType.SERIAL, BASE_PORT + 16),
        ],
    )
    async def test_connected(self, client, server, use_comm_type):
        """Test connection and data exchange."""
        assert await server.transport_listen()
        assert await client.transport_connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1
        server_connected = list(server.active_connections.values())[0]
        test_data = b"abcd"
        client.transport_send(test_data)
        await asyncio.sleep(0.5)
        assert server_connected.recv_buffer == test_data
        assert not client.recv_buffer
        server_connected.recv_buffer = b""
        if use_comm_type == CommType.UDP:
            sock = client.transport.get_extra_info("socket")
            addr = sock.getsockname()
            server_connected.transport_send(test_data, addr=addr)
        else:
            server_connected.transport_send(test_data)
        await asyncio.sleep(2)
        assert client.recv_buffer == test_data
        assert not server_connected.recv_buffer
        client.transport_close()
        server.transport_close()


class TestCommNullModem:  # pylint: disable=too-few-public-methods
    """Test null modem module."""

    def test_class_variables(self, nullmodem_server, nullmodem):
        """Test connection_made()."""
        assert nullmodem.client
        assert nullmodem.server
        assert nullmodem_server.client
        assert nullmodem_server.server
        nullmodem.__class__.client = self
        nullmodem.is_server = False
        nullmodem_server.__class__.server = self
        nullmodem_server.is_server = True

        assert nullmodem.client == nullmodem_server.client
        assert nullmodem.server == nullmodem_server.server
