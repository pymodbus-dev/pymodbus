"""Test transport."""
import asyncio
import time
from unittest import mock

import pytest

from pymodbus.transport import (
    CommType,
    ModbusProtocol,
)


FACTOR = 1.2 if not pytest.IS_WINDOWS else 4.2


class TestCommModbusProtocol:
    """Test for the transport module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port"""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "localhost"),
            (CommType.TLS, "localhost"),
            # (CommType.UDP, "localhost"), udp is connectionless.
            (CommType.SERIAL, "socket://localhost:5004"),
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
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "illegal_host"),
            (CommType.TLS, "illegal_host"),
            # (CommType.UDP, "illegal_host"), udp is connectionless.
            (CommType.SERIAL, "/dev/tty007pymodbus_5008"),
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
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "localhost"),
            (CommType.TLS, "localhost"),
            (CommType.UDP, "localhost"),
            (CommType.SERIAL, "socket://localhost:5012"),
        ],
    )
    async def test_listen(self, server):
        """Test listen()."""
        assert await server.transport_listen()
        assert server.transport
        server.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "illegal_host"),
            (CommType.TLS, "illegal_host"),
            (CommType.UDP, "illegal_host"),
            (CommType.SERIAL, "/dev/tty007pymodbus_5016"),
        ],
    )
    async def test_listen_not_ok(self, server):
        """Test listen()."""
        assert not await server.transport_listen()
        assert not server.transport
        server.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "localhost"),
            (CommType.TLS, "localhost"),
            (CommType.UDP, "localhost"),
            (CommType.SERIAL, "socket://localhost:5020"),
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
        await asyncio.sleep(1)
        assert client.recv_buffer == test_data
        assert not server_connected.recv_buffer
        client.transport_close()
        await asyncio.sleep(1)
        if use_comm_type != CommType.UDP:
            assert not server.active_connections
        server.transport_close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "localhost"),
            (CommType.TLS, "localhost"),
            # (CommType.UDP, "localhost"),  reuses same connection
            # (CommType.SERIAL, "socket://localhost:5020"), no multipoint
        ],
    )
    async def test_connected_multiple(self, client, server):
        """Test connection and data exchange."""
        client.comm_params.reconnect_delay = 0.0
        assert await server.transport_listen()
        assert await client.transport_connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1
        server_connected = list(server.active_connections.values())[0]

        client2 = ModbusProtocol(client.comm_params, False)
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
        await asyncio.sleep(0.5)
        assert not server.active_connections


class TestCommNullModem:
    """Test null modem module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port"""
        base_ports[__class__.__name__] += 2
        return base_ports[__class__.__name__]

    async def test_single_connection(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        connect = list(server.active_connections.values())[0]
        assert connect.transport.protocol == connect
        assert client.transport.protocol == client
        assert client.transport.other_modem == connect.transport
        assert connect.transport.other_modem == client.transport
        client.transport_close()
        server.transport_close()

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
        client.transport_close()
        server.transport_close()

    async def test_multi_connection(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        connect = list(server.active_connections.values())[0]
        new_params_server = server.comm_params.copy()
        new_params_server.source_address = (
            new_params_server.source_address[0],
            new_params_server.source_address[1] + 1,
        )
        new_params_client = client.comm_params.copy()
        new_params_client.port = new_params_server.source_address[1]
        server2 = ModbusProtocol(new_params_server, True)
        client2 = ModbusProtocol(new_params_client, False)
        await server2.transport_listen()
        await client2.transport_connect()
        connect2 = list(server2.active_connections.values())[0]
        assert connect.transport.protocol == connect
        assert connect.transport.other_modem == client.transport
        assert connect2.transport.protocol == connect2
        assert connect2.transport.other_modem == client2.transport
        assert client.transport.protocol == client
        assert client.transport.other_modem == connect.transport
        assert client2.transport.protocol == client2
        assert client2.transport.other_modem == connect2.transport
        for obj in (client, client2, server, server2):
            obj.transport_close()

    async def test_triangle_flow(self, server, client):
        """Test single connection."""
        await server.transport_listen()
        await client.transport_connect()
        connect = list(server.active_connections.values())[0]
        new_params_server = server.comm_params.copy()
        new_params_server.source_address = (
            new_params_server.source_address[0],
            new_params_server.source_address[1] + 1,
        )
        server2 = ModbusProtocol(new_params_server, True)
        new_params_client = client.comm_params.copy()
        new_params_client.port = new_params_server.source_address[1]
        client2 = ModbusProtocol(new_params_client, False)
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
        for obj in (client, client2, server, server2):
            obj.transport_close()
