"""Test transport."""
import asyncio
from unittest import mock


class TestReconnectTransport:
    """Test transport module, base part."""

    async def test_no_reconnect_call(self, client):
        """Test connection_lost()."""
        client.loop.create_connection = mock.AsyncMock(return_value=(None, None))
        await client.transport_connect()
        client.connection_lost(RuntimeError("Connection lost"))
        assert not client.reconnect_task
        assert client.loop.create_connection.call_count
        assert not client.reconnect_delay_current
        client.transport_close()

    async def test_reconnect_call(self, client, commparams):
        """Test connection_lost()."""
        client.loop.create_connection = mock.AsyncMock(return_value=(None, None))
        await client.transport_connect()
        client.connection_made(mock.Mock())
        client.connection_lost(RuntimeError("Connection lost"))
        assert client.reconnect_task
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.reconnect_task
        assert client.loop.create_connection.call_count == 2
        assert client.reconnect_delay_current == commparams.reconnect_delay * 2
        client.transport_close()

    async def test_multi_reconnect_call(self, client, commparams):
        """Test connection_lost()."""
        client.loop.create_connection = mock.AsyncMock(return_value=(None, None))
        await client.transport_connect()
        client.connection_made(mock.Mock())
        client.connection_lost(RuntimeError("Connection lost"))
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.loop.create_connection.call_count == 2
        assert client.reconnect_delay_current == commparams.reconnect_delay * 2
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.loop.create_connection.call_count == 3
        assert client.reconnect_delay_current == commparams.reconnect_delay_max
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.loop.create_connection.call_count >= 4
        assert client.reconnect_delay_current == commparams.reconnect_delay_max
        client.transport_close()

    async def test_reconnect_call_ok(self, client, commparams):
        """Test connection_lost()."""
        client.loop.create_connection = mock.AsyncMock(
            return_value=(mock.Mock(), mock.Mock())
        )
        await client.transport_connect()
        client.connection_made(mock.Mock())
        client.connection_lost(RuntimeError("Connection lost"))
        await asyncio.sleep(client.reconnect_delay_current * 1.8)
        assert client.loop.create_connection.call_count == 2
        assert client.reconnect_delay_current == commparams.reconnect_delay
        assert not client.reconnect_task
        client.transport_close()
