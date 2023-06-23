"""Test transport."""
import asyncio
import time
from unittest import mock

import pytest

from pymodbus.transport.transport import NULLMODEM_HOST, CommType, Transport


BASE_PORT = 6100
FACTOR = 1.2 if not pytest.IS_WINDOWS else 2.2


class TestCommTransport:
    """Test for the transport module."""

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host", "use_port"),
        [
            (CommType.TCP, "localhost", BASE_PORT + 1),
            (CommType.TLS, "localhost", BASE_PORT + 2),
            # (CommType.UDP, "localhost", BASE_PORT + 3), udp is connectionless.
            (
                CommType.SERIAL,
                f"socket://localhost:{BASE_PORT + 4}",
                BASE_PORT + 4,
            ),
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
        ("use_comm_type", "use_host", "use_port"),
        [
            (CommType.TCP, "illegal_host", BASE_PORT + 5),
            (CommType.TLS, "illegal_host", BASE_PORT + 6),
            # (CommType.UDP, "illegal_host", BASE_PORT + 7), udp is connectionless.
            (CommType.SERIAL, f"/dev/tty007pymodbus_{BASE_PORT + 8}", BASE_PORT + 8),
        ],
    )
    async def test_connect_not_ok(self, client):
        """Test connect()."""
        start = time.time()
        assert not await client.transport_connect()
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * FACTOR
        client.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host", "use_port"),
        [
            (CommType.TCP, "localhost", BASE_PORT + 9),
            (CommType.TLS, "localhost", BASE_PORT + 10),
            (CommType.UDP, "localhost", BASE_PORT + 11),
            (CommType.SERIAL, f"socket://localhost:{BASE_PORT + 12}", BASE_PORT + 12),
        ],
    )
    async def test_listen(self, server):
        """Test listen()."""
        assert await server.transport_listen()
        assert server.transport
        server.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host", "use_port"),
        [
            (CommType.TCP, "illegal_host", BASE_PORT + 13),
            (CommType.TLS, "illegal_host", BASE_PORT + 14),
            (CommType.UDP, "illegal_host", BASE_PORT + 15),
            (CommType.SERIAL, f"/dev/tty007pymodbus_{BASE_PORT + 16}", BASE_PORT + 16),
        ],
    )
    async def test_listen_not_ok(self, server):
        """Test listen()."""
        assert not await server.transport_listen()
        assert not server.transport
        server.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host", "use_port"),
        [
            (CommType.TCP, "localhost", BASE_PORT + 17),
            (CommType.TLS, "localhost", BASE_PORT + 18),
            (CommType.UDP, "localhost", BASE_PORT + 19),
            (CommType.SERIAL, f"socket://localhost:{BASE_PORT + 20}", BASE_PORT + 20),
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

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host", "use_port"),
        [
            (CommType.TCP, "localhost", BASE_PORT + 21),
        ],
    )
    async def test_connected_multiple(self, client, server, commparams):
        """Test connection and data exchange."""
        assert await server.transport_listen()
        assert await client.transport_connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1
        server_connected = list(server.active_connections.values())[0]

        c2_params = commparams.copy()
        c2_params.port = client.comm_params.port + 1
        client2 = Transport(commparams, False)
        client2.callback_connected = mock.Mock()
        client2.callback_disconnected = mock.Mock()
        client2.callback_data = mock.Mock(return_value=0)

        assert await client2.transport_connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 2
        server2_connected = list(server.active_connections.values())[1]

        test_data = b"abcd"
        client.transport_send(test_data)
        test2_data = b"efghij"
        client2.transport_send(test2_data)
        await asyncio.sleep(0.5)
        assert server_connected.recv_buffer == test_data
        assert server2_connected.recv_buffer == test2_data

        server_connected.transport_send(test2_data)
        server2_connected.transport_send(test_data)
        await asyncio.sleep(0.5)
        assert client.recv_buffer == test2_data
        assert client2.recv_buffer == test_data

        client.transport_close()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1

        client2.transport_send(test_data)
        await asyncio.sleep(0.5)
        assert server2_connected.recv_buffer == test2_data + test_data
        client2.transport_close()
        server.transport_close()


class TestCommNullModem:
    """Test null modem module."""

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_single_connection(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        assert server.transport.protocol == server
        assert server.transport.other == client.transport
        assert client.transport.listening == -1
        assert client.transport.protocol == client
        assert client.transport.other == server.transport
        client.transport_close()

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_single_flow(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        server.callback_data = mock.Mock(return_value=0)
        client.callback_data = mock.Mock(return_value=0)
        test_data = b"abcd"
        test_data2 = b"efgh"
        client.transport_send(test_data)
        server.transport_send(test_data2)
        assert server.recv_buffer == test_data
        assert client.recv_buffer == test_data2
        client.callback_data.assert_called_once()
        server.callback_data.assert_called_once()

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_multi_connection(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        server2 = Transport(server.comm_params, True)
        client2 = Transport(client.comm_params, False)
        await server2.transport_listen()
        await client2.transport_connect()

        assert server.transport.protocol == server
        assert server.transport.other == client.transport
        assert server2.transport.protocol == server2
        assert server2.transport.other == client2.transport
        assert client.transport.protocol == client
        assert client.transport.other == server.transport
        assert client2.transport.protocol == client2
        assert client2.transport.other == server2.transport
        assert client.transport.listening == -1
        client.transport_close()
        client2.transport_close()

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_triangle_flow(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        server2 = Transport(server.comm_params, True)
        client2 = Transport(client.comm_params, False)
        await server2.transport_listen()
        await client2.transport_connect()
        server.callback_data = mock.Mock(return_value=0)
        client.callback_data = mock.Mock(return_value=0)
        client2.callback_data = mock.Mock(return_value=0)
        server2.callback_data = mock.Mock(return_value=0)
        test_data = b"abcd"
        test_data2 = b"efgh"
        test_data3 = b"ijkl"
        test_data4 = b"mnop"
        client.transport_send(test_data)
        client2.transport_send(test_data2)
        server.transport_send(test_data3)
        server2.transport_send(test_data4)
        assert server.recv_buffer == test_data
        assert server2.recv_buffer == test_data2
        assert client.recv_buffer == test_data3
        assert client2.recv_buffer == test_data4
        client.callback_data.assert_called_once()
        client2.callback_data.assert_called_once()
        server.callback_data.assert_called_once()
        server2.callback_data.assert_called_once()
