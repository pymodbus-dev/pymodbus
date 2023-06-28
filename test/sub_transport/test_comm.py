"""Test transport."""
import asyncio
import time
from unittest import mock

import pytest

from pymodbus.transport.transport import NULLMODEM_HOST, CommType, ModbusProtocol


BASE_PORT = 6100
FACTOR = 1.2 if not pytest.IS_WINDOWS else 2.2


class TestCommModbusProtocol:
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
        await asyncio.sleep(2)
        if use_comm_type != CommType.UDP:
            assert not len(server.active_connections)
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
        client2 = ModbusProtocol(commparams, False)
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
        assert not len(server.active_connections)


class TestCommNullModem:
    """Test null modem module."""

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_single_connection(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        connect = list(server.active_connections.values())[0]
        assert connect.transport.protocol == connect
        assert client.transport.protocol == client
        assert client.transport.other_transport == connect.transport
        assert connect.transport.other_transport == client.transport
        client.transport_close()

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_single_flow(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        connect = list(server.active_connections.values())[0]
        connect.callback_data = mock.Mock(return_value=0)
        client.callback_data = mock.Mock(return_value=0)
        test_data = b"abcd"
        test_data2 = b"efgh"
        client.transport_send(test_data)
        connect.transport_send(test_data2)
        assert connect.recv_buffer == test_data
        assert client.recv_buffer == test_data2
        client.callback_data.assert_called_once()
        connect.callback_data.assert_called_once()

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_multi_connection(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        connect = list(server.active_connections.values())[0]
        server2 = ModbusProtocol(server.comm_params, True)
        client2 = ModbusProtocol(client.comm_params, False)
        await server2.transport_listen()
        await client2.transport_connect()
        connect2 = list(server2.active_connections.values())[0]

        assert connect.transport.protocol == connect
        assert connect.transport.other_transport == client.transport
        assert connect2.transport.protocol == connect2
        assert connect2.transport.other_transport == client2.transport
        assert client.transport.protocol == client
        assert client.transport.other_transport == connect.transport
        assert client2.transport.protocol == client2
        assert client2.transport.other_transport == connect2.transport
        client.transport_close()
        client2.transport_close()

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_triangle_flow(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        connect = list(server.active_connections.values())[0]
        server2 = ModbusProtocol(server.comm_params, True)
        client2 = ModbusProtocol(client.comm_params, False)
        await server2.transport_listen()
        await client2.transport_connect()
        connect2 = list(server2.active_connections.values())[0]
        connect.callback_data = mock.Mock(return_value=0)
        client.callback_data = mock.Mock(return_value=0)
        client2.callback_data = mock.Mock(return_value=0)
        connect2.callback_data = mock.Mock(return_value=0)
        test_data = b"abcd"
        test_data2 = b"efgh"
        test_data3 = b"ijkl"
        test_data4 = b"mnop"
        client.transport_send(test_data)
        client2.transport_send(test_data2)
        connect.transport_send(test_data3)
        connect2.transport_send(test_data4)
        assert connect.recv_buffer == test_data
        assert connect2.recv_buffer == test_data2
        assert client.recv_buffer == test_data3
        assert client2.recv_buffer == test_data4
        client.callback_data.assert_called_once()
        client2.callback_data.assert_called_once()
        connect.callback_data.assert_called_once()
        connect2.callback_data.assert_called_once()
