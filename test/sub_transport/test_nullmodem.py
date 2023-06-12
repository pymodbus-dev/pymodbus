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

    async def xtest_nullmodem_connect(self, nullmodem, nullmodem_server):
        """Test connection_made()."""
        nullmodem.loop = None
        assert not await nullmodem.transport_connect()
        assert not nullmodem.other_end
        assert nullmodem.loop
        nullmodem.cb_connection_made.assert_not_called()
        nullmodem.cb_connection_lost.assert_not_called()
        nullmodem.cb_handle_data.assert_not_called()

        nullmodem_server.loop = None
        assert await nullmodem_server.transport_listen()
        assert nullmodem_server.is_server
        assert not nullmodem_server.client
        assert nullmodem_server.server
        assert nullmodem.loop
        nullmodem_server.cb_connection_made.assert_not_called()
        nullmodem_server.cb_connection_lost.assert_not_called()
        nullmodem_server.cb_handle_data.assert_not_called()

        assert await nullmodem.transport_connect()
        assert not nullmodem.is_server
        assert nullmodem.client
        assert nullmodem.server
        assert nullmodem.loop
        nullmodem.cb_connection_made.assert_called_once()
        nullmodem.cb_connection_lost.assert_not_called()
        nullmodem.cb_handle_data.assert_not_called()
        nullmodem_server.cb_connection_made.assert_called_once()
        nullmodem.cb_connection_lost.assert_not_called()
        nullmodem.cb_handle_data.assert_not_called()

    async def xtest_nullmodem_close(self, transport):
        """Test close()."""

    async def xtest_nullmodem_data(self, transport):
        """Test data_received."""
        transport.cb_handle_data = mock.MagicMock(return_value=2)
        transport.data_received(b"123456")
        transport.cb_handle_data.assert_called_once()
        assert transport.recv_buffer == b"3456"
        transport.data_received(b"789")
        assert transport.recv_buffer == b"56789"

    async def xtest_nullmodem_send(self, transport, params):
        """Test send()."""
        transport.transport = mock.AsyncMock()
        await transport.send(b"abc")

        transport.setup_udp(False, params.host, params.port)
        await transport.send(b"abc")
        transport.close()
