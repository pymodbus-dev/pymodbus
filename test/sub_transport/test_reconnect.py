"""Test transport."""
import asyncio
from unittest import mock

import pytest


class TestReconnectTransport:
    """Test transport module, base part."""

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_no_reconnect_call(self, transport, use_port, commparams):
        """Test connection_lost()."""
        transport.setup_tcp(False, "localhost", use_port)
        mocker = mock.AsyncMock(return_value=(None, None))
        transport.loop.create_connection = mocker
        transport.connection_made(mock.Mock())
        assert not mocker.call_count
        assert transport.reconnect_delay_current == commparams.reconnect_delay
        transport.connection_lost(RuntimeError("Connection lost"))
        assert not mocker.call_count
        assert transport.reconnect_delay_current == commparams.reconnect_delay
        transport.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_reconnect_call(self, transport, use_port, commparams):
        """Test connection_lost()."""
        transport.setup_tcp(False, "localhost", use_port)
        mocker = mock.AsyncMock(return_value=(None, None))
        transport.loop.create_connection = mocker
        transport.connection_made(mock.Mock())
        transport.connection_lost(RuntimeError("Connection lost"))
        await asyncio.sleep(transport.reconnect_delay_current * 1.8)
        assert mocker.call_count == 1
        assert transport.reconnect_delay_current == commparams.reconnect_delay * 2
        transport.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_multi_reconnect_call(self, transport, use_port, commparams):
        """Test connection_lost()."""
        transport.setup_tcp(False, "localhost", use_port)
        mocker = mock.AsyncMock(return_value=(None, None))
        transport.loop.create_connection = mocker
        transport.connection_made(mock.Mock())
        transport.connection_lost(RuntimeError("Connection lost"))
        await asyncio.sleep(transport.reconnect_delay_current * 1.8)
        assert mocker.call_count == 1
        assert transport.reconnect_delay_current == commparams.reconnect_delay * 2
        await asyncio.sleep(transport.reconnect_delay_current * 1.8)
        assert mocker.call_count == 2
        assert transport.reconnect_delay_current == commparams.reconnect_delay_max
        await asyncio.sleep(transport.reconnect_delay_current * 1.8)
        assert mocker.call_count >= 3
        assert transport.reconnect_delay_current == commparams.reconnect_delay_max
        transport.close()

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_reconnect_call_ok(self, transport, use_port, commparams):
        """Test connection_lost()."""
        transport.setup_tcp(False, "localhost", use_port)
        mocker = mock.AsyncMock(return_value=(mock.Mock(), mock.Mock()))
        transport.loop.create_connection = mocker
        transport.connection_made(mock.Mock())
        transport.connection_lost(RuntimeError("Connection lost"))
        await asyncio.sleep(transport.reconnect_delay_current * 1.8)
        assert mocker.call_count == 1
        assert transport.reconnect_delay_current == commparams.reconnect_delay
        assert not transport.reconnect_task
        transport.close()
