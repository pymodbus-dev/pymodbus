"""Test transport."""
from unittest import mock

from pymodbus.transport.nullmodem import DummyTransport


class TestNullModemTransport:
    """Test null modem module."""

    async def test_str_magic(self, nullmodem, params):
        """Test magic."""
        str(nullmodem)
        assert str(nullmodem) == f"NullModem({params.comm_name})"

    def test_DummyTransport(self):
        """Test DummyTransport class."""
        socket = DummyTransport()
        socket.close()
        socket.get_protocol()
        socket.is_closing()
        socket.set_protocol(None)
        socket.abort()

    async def test_transport_connect(self, transport, commparams):
        """Test connection_made()."""
        transport.loop = None
        transport.connection_made(DummyTransport())
        assert transport.transport
        assert not transport.recv_buffer
        assert not transport.reconnect_task
        assert transport.reconnect_delay_current == commparams.reconnect_delay
        transport.cb_connection_made.assert_called_once()
        transport.cb_connection_lost.assert_not_called()
        transport.cb_handle_data.assert_not_called()
        transport.close()

    async def test_close(self, transport):
        """Test close()."""

    async def test_datagram(self, transport):
        """Test datagram_received()."""
        transport.data_received = mock.MagicMock()
        transport.datagram_received(b"abc", "127.0.0.1")
        transport.data_received.assert_called_once()

    async def test_data(self, transport):
        """Test data_received."""
        transport.cb_handle_data = mock.MagicMock(return_value=2)
        transport.data_received(b"123456")
        transport.cb_handle_data.assert_called_once()
        assert transport.recv_buffer == b"3456"
        transport.data_received(b"789")
        assert transport.recv_buffer == b"56789"

    async def test_send(self, transport, params):
        """Test send()."""
        transport.transport = mock.AsyncMock()
        await transport.send(b"abc")

        transport.setup_udp(False, params.host, params.port)
        await transport.send(b"abc")
        transport.close()
