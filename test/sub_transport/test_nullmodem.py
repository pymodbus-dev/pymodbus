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

    def test_class_variables(self, nullmodem, nullmodem_server):
        """Test connection_made()."""
        assert not nullmodem.nullmodem_client
        assert not nullmodem.nullmodem_server
        assert not nullmodem_server.nullmodem_client
        assert not nullmodem_server.nullmodem_server
        nullmodem.__class__.nullmodem_client = self
        nullmodem.is_server = False
        nullmodem_server.__class__.nullmodem_server = self
        nullmodem_server.is_server = True

        assert nullmodem.nullmodem_client == nullmodem_server.nullmodem_client
        assert nullmodem.nullmodem_server == nullmodem_server.nullmodem_server

    async def test_transport_connect(self, nullmodem):
        """Test connection_made()."""
        nullmodem.loop = None
        assert not await nullmodem.transport_connect()
        assert not nullmodem.nullmodem_server
        assert not nullmodem.nullmodem_client
        assert nullmodem.loop
        nullmodem.cb_connection_made.assert_not_called()
        nullmodem.cb_connection_lost.assert_not_called()
        nullmodem.cb_handle_data.assert_not_called()

    async def test_transport_listen(self, nullmodem_server):
        """Test connection_made()."""
        nullmodem_server.loop = None
        assert await nullmodem_server.transport_listen()
        assert nullmodem_server.is_server
        assert nullmodem_server.nullmodem_server
        assert not nullmodem_server.nullmodem_client
        assert nullmodem_server.loop
        nullmodem_server.cb_connection_made.assert_not_called()
        nullmodem_server.cb_connection_lost.assert_not_called()
        nullmodem_server.cb_handle_data.assert_not_called()

    async def test_connected(self, nullmodem, nullmodem_server):
        """Test connection is correct."""
        assert await nullmodem_server.transport_listen()
        assert await nullmodem.transport_connect()
        assert nullmodem.nullmodem_client
        assert nullmodem.nullmodem_server
        assert nullmodem.loop
        assert not nullmodem.is_server
        assert nullmodem_server.is_server
        nullmodem.cb_connection_made.assert_called_once()
        nullmodem.cb_connection_lost.assert_not_called()
        nullmodem.cb_handle_data.assert_not_called()
        nullmodem_server.cb_connection_made.assert_called_once()
        nullmodem_server.cb_connection_lost.assert_not_called()
        nullmodem_server.cb_handle_data.assert_not_called()

    async def test_client_close(self, nullmodem, nullmodem_server):
        """Test close()."""
        assert await nullmodem_server.transport_listen()
        assert await nullmodem.transport_connect()
        nullmodem.close()
        assert not nullmodem.nullmodem_client
        assert not nullmodem.nullmodem_server
        nullmodem.cb_connection_made.assert_called_once()
        nullmodem.cb_connection_lost.assert_called_once()
        nullmodem.cb_handle_data.assert_not_called()
        nullmodem_server.cb_connection_made.assert_called_once()
        nullmodem_server.cb_connection_lost.assert_called_once()
        nullmodem_server.cb_handle_data.assert_not_called()

    async def test_server_close(self, nullmodem, nullmodem_server):
        """Test close()."""
        assert await nullmodem_server.transport_listen()
        assert await nullmodem.transport_connect()
        nullmodem_server.close()
        assert not nullmodem.nullmodem_client
        assert not nullmodem.nullmodem_server
        nullmodem.cb_connection_made.assert_called_once()
        nullmodem.cb_connection_lost.assert_called_once()
        nullmodem.cb_handle_data.assert_not_called()
        nullmodem_server.cb_connection_made.assert_called_once()
        nullmodem_server.cb_connection_lost.assert_called_once()
        nullmodem_server.cb_handle_data.assert_not_called()

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
