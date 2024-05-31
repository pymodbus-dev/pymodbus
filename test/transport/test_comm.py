"""Test transport."""
import asyncio
import platform
import time
from unittest import mock

import pytest

from pymodbus.logging import Log
from pymodbus.transport import (
    CommType,
    ModbusProtocol,
)
from pymodbus.transport.serialtransport import SerialTransport


FACTOR = 1.2 if platform.system().lower() != "windows" else 4.2


class TestTransportComm:
    """Test for the transport module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port."""
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
    async def test_connect(self, client, use_port):
        """Test connect()."""
        Log.debug("test_connect {}", use_port)
        start = time.time()
        assert not await client.connect()
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * FACTOR
        client.close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "illegal_host"),
            (CommType.TLS, "illegal_host"),
            # (CommType.UDP, "illegal_host"), udp is connectionless.
            (CommType.SERIAL, "/dev/tty007pymodbus_5008"),
        ],
    )
    async def test_connect_not_ok(self, client, use_port):
        """Test connect()."""
        Log.debug("test_connect_not_ok {}", use_port)
        start = time.time()
        assert not await client.connect()
        delta = time.time() - start
        assert delta < client.comm_params.timeout_connect * FACTOR
        client.close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "localhost"),
            (CommType.TLS, "localhost"),
            (CommType.UDP, "localhost"),
            (CommType.SERIAL, "socket://localhost:5012"),
        ],
    )
    async def test_listen(self, server, use_port):
        """Test listen()."""
        Log.debug("test_listen {}", use_port)
        assert await server.listen()
        assert server.transport
        server.close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "illegal_host"),
            (CommType.TLS, "illegal_host"),
            (CommType.UDP, "illegal_host"),
            (CommType.SERIAL, "/dev/tty007pymodbus_5016"),
        ],
    )
    async def test_listen_not_ok(self, server, use_port):
        """Test listen()."""
        Log.debug("test_listen_not_ok {}", use_port)
        assert not await server.listen()
        assert not server.transport
        server.close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "localhost"),
            (CommType.TLS, "localhost"),
            (CommType.UDP, "localhost"),
            (CommType.SERIAL, "socket://localhost:7302"),
        ],
    )
    async def test_connected(self, client, server, use_comm_type, use_port):
        """Test connection and data exchange."""
        Log.debug("test_connected {}", use_port)
        assert await server.listen()
        assert await client.connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1
        server_connected = list(server.active_connections.values())[0]
        test_data = b"abcd"
        client.send(test_data)
        await asyncio.sleep(0.5)
        assert server_connected.recv_buffer == test_data
        assert not client.recv_buffer
        server_connected.recv_buffer = b""
        if use_comm_type == CommType.UDP:
            sock = client.transport.get_extra_info("socket")
            addr = sock.getsockname()
            server_connected.send(test_data, addr=addr)
        else:
            server_connected.send(test_data)
        await asyncio.sleep(1)
        assert client.recv_buffer == test_data
        assert not server_connected.recv_buffer
        client.close()
        await asyncio.sleep(1)
        if use_comm_type != CommType.UDP:
            assert not server.active_connections
        server.close()

    def wrapped_write(self, data):
        """Wrap serial write, to split parameters."""
        return self.serial_write(data[:2])

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.SERIAL, "socket://localhost:7303"),
        ],
    )
    async def test_split_serial_packet(self, client, server, use_port):
        """Test connection and data exchange."""
        Log.debug("test_split_serial_packet {}", use_port)
        assert await server.listen()
        assert await client.connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1
        server_connected = list(server.active_connections.values())[0]
        test_data = b"abcd"

        self.serial_write = (  # pylint: disable=attribute-defined-outside-init
            client.transport.sync_serial.write
        )
        with mock.patch.object(
            client.transport.sync_serial, "write", wraps=self.wrapped_write
        ):
            client.send(test_data)
            await asyncio.sleep(0.5)
        assert server_connected.recv_buffer == test_data
        assert not client.recv_buffer
        client.close()
        server.close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.SERIAL, "socket://localhost:7300"),
        ],
    )
    async def test_serial_poll(self, client, server, use_port):
        """Test connection and data exchange."""
        Log.debug("test_serial_poll {}", use_port)
        assert await server.listen()
        SerialTransport.force_poll = True
        assert await client.connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1
        server_connected = list(server.active_connections.values())[0]
        test_data = b"abcd" * 1000
        client.send(test_data)
        await asyncio.sleep(0.5)
        assert server_connected.recv_buffer == test_data
        assert not client.recv_buffer
        client.close()
        server.close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "localhost"),
            (CommType.TLS, "localhost"),
            # (CommType.UDP, "localhost"),  reuses same connection
            # (CommType.SERIAL, "socket://localhost:7301"), no multipoint
        ],
    )
    async def test_connected_multiple(self, client, server, use_port):
        """Test connection and data exchange."""
        Log.debug("test_connected {}", use_port)
        client.comm_params.reconnect_delay = 0.0
        assert await server.listen()
        assert await client.connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1
        server_connected = list(server.active_connections.values())[0]

        client2 = ModbusProtocol(client.comm_params, False)
        client2.callback_connected = mock.Mock()
        client2.callback_disconnected = mock.Mock()
        client2.callback_data = mock.Mock(return_value=0)
        assert await client2.connect()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 2
        server2_connected = list(server.active_connections.values())[1]

        test_data = b"abcd"
        client.send(test_data)
        test2_data = b"efghij"
        client2.send(test2_data)
        await asyncio.sleep(0.5)
        assert server_connected.recv_buffer == test_data
        assert server2_connected.recv_buffer == test2_data

        server_connected.send(test2_data)
        server2_connected.send(test_data)
        await asyncio.sleep(0.5)
        assert client.recv_buffer == test2_data
        assert client2.recv_buffer == test_data

        client.close()
        await asyncio.sleep(0.5)
        assert len(server.active_connections) == 1

        client2.send(test_data)
        await asyncio.sleep(0.5)
        assert server2_connected.recv_buffer == test2_data + test_data
        client2.close()
        server.close()
        await asyncio.sleep(0.5)
        assert not server.active_connections
