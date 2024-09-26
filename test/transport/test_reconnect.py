"""Test transport."""
import asyncio
from unittest import mock

import pytest

from pymodbus.transport import NULLMODEM_HOST, CommType


class TestTransportReconnect:
    """Test transport module, base part."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port."""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    async def test_no_reconnect_call(self, client):
        """Test connection_lost()."""
        client.loop = asyncio.get_running_loop()
        client.call_create = mock.AsyncMock(return_value=(None, None))
        await client.connect()
        client.connection_lost(RuntimeError("Connection lost"))
        assert not client.reconnect_task
        assert not client.reconnect_delay_current
        assert client.call_create.called
        client.close()

    async def test_reconnect_call(self, client):
        """Test connection_lost()."""
        client.loop = asyncio.get_running_loop()
        client.call_create = mock.AsyncMock(return_value=(None, None))
        await client.connect()
        client.connection_made(mock.Mock())
        client.connection_lost(RuntimeError("Connection lost"))
        assert client.reconnect_task
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.reconnect_task
        assert client.call_create.call_count == 2
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay * 2
        client.close()

    async def test_multi_reconnect_call(self, client):
        """Test connection_lost()."""
        client.loop = asyncio.get_running_loop()
        client.call_create = mock.AsyncMock(return_value=(None, None))
        await client.connect()
        client.connection_made(mock.Mock())
        client.connection_lost(RuntimeError("Connection lost"))
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.call_create.call_count == 2
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay * 2
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.call_create.call_count == 3
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay_max
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.call_create.call_count >= 4
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay_max
        client.close()

    async def test_reconnect_call_ok(self, client):
        """Test connection_lost()."""
        client.loop = asyncio.get_running_loop()
        client.call_create = mock.AsyncMock(return_value=(mock.Mock(), mock.Mock()))
        await client.connect()
        client.connection_made(mock.Mock())
        client.connection_lost(RuntimeError("Connection lost"))
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.call_create.call_count == 2
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay
        assert not client.reconnect_task
        client.close()

    @pytest.mark.parametrize(
        ("use_comm_type", "use_host"),
        [
            (CommType.TCP, "localhost"),
            (CommType.TLS, "localhost"),
            (CommType.UDP, "localhost"),
            (CommType.SERIAL, NULLMODEM_HOST),
        ],
    )
    async def test_listen_disconnect(self, server):
        """Test listen()."""
        assert await server.listen()
        assert server.transport
        server.connection_lost(None)
        assert not server.transport
        await asyncio.sleep(1.5)
        assert server.transport
        server.close()
        assert not server.transport

    async def test_relisten_call(self, server):
        """Test connection_lost()."""
        server.loop = asyncio.get_running_loop()
        await server.listen()
        server.connection_lost(RuntimeError("Listener disconnected lost"))
        assert server.reconnect_task
        server.close()

