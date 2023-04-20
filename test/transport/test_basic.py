"""Test transport."""
import asyncio
from unittest import mock

from pymodbus.transaction import ModbusSocketFramer
from pymodbus.transport.transport import BaseTransport


class TestTransportBase:
    """Test for the transport module."""

    base_comm_name = "test comm"
    base_framer = ModbusSocketFramer
    base_reconnect_delay = 10
    base_reconnect_delay_max = 15
    base_timeout_connect = 20
    base_timeout_comm = 25

    class dummy_transport:
        """Transport class for test."""

        def __init__(self):
            """Initialize."""
            self.abort = mock.MagicMock()
            self.close = mock.MagicMock()

    @classmethod
    def setup_BaseTransport(self):
        """Create base object."""
        base = BaseTransport(
            self.base_comm_name,
            self.base_framer,
            self.base_reconnect_delay,
            self.base_reconnect_delay_max,
            self.base_timeout_connect,
            self.base_timeout_comm,
        )
        base.cb_connection_lost = mock.MagicMock()
        base.cb_connection_made = mock.MagicMock()
        base.cb_handle_data = mock.MagicMock()
        return base

    def test_properties(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        assert self.base_comm_name == base.comm_name
        assert self.base_framer == base.framer
        assert self.base_reconnect_delay == base.reconnect_delay
        assert self.base_reconnect_delay_max == base.reconnect_delay_max
        assert self.base_timeout_connect == base.timeout_connect
        assert self.base_timeout_comm == base.timeout_comm
        assert self.base_reconnect_delay == base.reconnect_delay_current

    async def test_magic(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        base.close = mock.MagicMock()
        async with base:
            pass
        base.close.assert_called_once()
        assert str(base) == f"BaseTransport({self.base_comm_name})"

    def test_connection_made(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        transport = self.dummy_transport()
        base.connection_made(transport)
        assert base.transport == transport
        assert not base.recv_buffer
        assert not base.reconnect_timer
        base.cb_connection_made.assert_called_once()
        base.cb_connection_lost.assert_not_called()
        base.cb_handle_data.assert_not_called()

    def test_connection_lost(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        transport = self.dummy_transport()
        base.connection_lost(transport)
        assert not base.transport
        assert not base.recv_buffer
        assert base.reconnect_timer
        base.cb_connection_made.assert_not_called()
        base.cb_connection_lost.assert_called_once()
        base.cb_handle_data.assert_not_called()
        base.close()

    def test_close_simple(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        transport = self.dummy_transport()
        base.connection_made(transport)
        base.cb_connection_made.reset_mock()
        base.cb_connection_lost.reset_mock()
        base.cb_handle_data.reset_mock()
        base.recv_buffer = b"abc"
        base.reconnect_timer = mock.MagicMock()
        base.close()
        transport.abort.assert_called_once()
        transport.close.assert_called_once()
        base.cb_connection_made.assert_not_called()
        base.cb_connection_lost.assert_not_called()
        base.cb_handle_data.assert_not_called()
        assert not base.recv_buffer
        assert not base.reconnect_timer

    def test_close_reconnect(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        transport = self.dummy_transport()
        base.connection_made(transport)
        base.reconnect_timer = None
        base.close(reconnect=True)
        assert base.reconnect_timer
        base.close()
        assert not base.reconnect_timer

    def test_reset_delay(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        base.reconnect_delay_current = self.base_reconnect_delay + 1
        base.reset_delay()
        assert base.reconnect_delay_current == self.base_reconnect_delay

    async def test_connect(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        base.reconnect_delay_current = self.base_reconnect_delay + 1
        base.close(reconnect=True)
        base.complete_connect()
        assert not base.reconnect_timer
        assert base.reconnect_delay_current == self.base_reconnect_delay
        base.close()
        base.reset_delay()
        base.complete_connect(connected=False)
        assert base.reconnect_timer
        assert base.reconnect_delay_current == self.base_reconnect_delay_max

    async def test_reconnect(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        transport = self.dummy_transport()
        base.connection_made(transport)
        base.connect = mock.MagicMock()
        base.close(reconnect=True)
        await asyncio.sleep((self.base_reconnect_delay + 1) / 1000)
        base.connect.assert_called_once()
        assert base.reconnect_timer
        base.close()

    async def test_datagram(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        base.data_received = mock.MagicMock()
        base.datagram_received(b"abc", "127.0.0.1")
        base.data_received.assert_called_once()
        base.close()

    async def test_receive(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        base.cb_handle_data = mock.MagicMock(return_value=2)
        base.data_received(b"123456")
        base.cb_handle_data.assert_called_once()
        assert base.recv_buffer == b"3456"
        base.data_received(b"789")
        assert base.recv_buffer == b"56789"
        base.close()

    async def test_send(self):
        """Test properties."""
        base = self.setup_BaseTransport()
        await base.send(b"abc")
        base.close()
