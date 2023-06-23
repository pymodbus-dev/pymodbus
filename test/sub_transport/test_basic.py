"""Test transport."""
import asyncio
from unittest import mock

import pytest

from pymodbus.transport.transport import NULLMODEM_HOST, CommType, NullModem, Transport


COMM_TYPES = [
    CommType.TCP,
    CommType.TLS,
    CommType.UDP,
    CommType.SERIAL,
]


class TestBasicTransport:
    """Test transport module."""

    @pytest.mark.parametrize("use_comm_type", COMM_TYPES)
    async def test_init(self, client, server, commparams):
        """Test init()"""
        if commparams.comm_type == CommType.SERIAL:
            client.comm_params.host = commparams.host
            server.comm_params.comm_type = commparams.comm_type
        client.comm_params.sslctx = None
        assert client.comm_params == commparams
        assert client.unique_id == str(id(client))
        assert not client.is_server
        server.comm_params.sslctx = None
        assert server.comm_params == commparams
        assert server.unique_id == str(id(server))
        assert server.is_server

        commparams.host = NULLMODEM_HOST
        Transport(commparams, False)
        if commparams.comm_type == CommType.SERIAL:
            commparams.host = "socket://127.0.0.1:6301"
            Transport(commparams, True)

    async def test_connect(self, client, dummy_transport):
        """Test properties."""
        client.loop = None
        client.call_create = mock.AsyncMock(return_value=(dummy_transport, None))
        assert await client.transport_connect()
        assert client.loop
        client.call_create.side_effect = asyncio.TimeoutError("test")
        assert not await client.transport_connect()

    async def test_listen(self, server, dummy_transport):
        """Test listen_tcp()."""
        server.call_create = mock.AsyncMock(return_value=(dummy_transport, None))
        server.loop = None
        assert await server.transport_listen()
        server.call_create.side_effect = OSError("testing")
        assert not await server.transport_listen()

    async def test_connection_made(self, client, commparams, dummy_transport):
        """Test connection_made()."""
        client.connection_made(dummy_transport)
        assert client.transport
        assert not client.recv_buffer
        assert not client.reconnect_task
        assert client.reconnect_delay_current == commparams.reconnect_delay
        client.callback_connected.assert_called_once()

    async def test_connection_lost(self, client, dummy_transport):
        """Test connection_lost()."""
        client.connection_lost(RuntimeError("not implemented"))
        client.connection_made(dummy_transport)
        client.connection_lost(RuntimeError("not implemented"))
        assert not client.transport
        assert not client.recv_buffer
        assert client.reconnect_task
        client.callback_disconnected.assert_called_once()
        client.transport_close()
        assert not client.reconnect_task
        assert not client.reconnect_delay_current

    async def test_data_received(self, client):
        """Test data_received."""
        client.callback_data = mock.MagicMock(return_value=2)
        client.data_received(b"123456")
        client.callback_data.assert_called_once()
        assert client.recv_buffer == b"3456"
        client.data_received(b"789")
        assert client.recv_buffer == b"56789"

    async def test_datagram(self, client):
        """Test datagram_received()."""
        client.callback_data = mock.MagicMock()
        client.datagram_received(b"abc", "127.0.0.1")
        client.callback_data.assert_called_once()

    async def test_eof_received(self, client):
        """Test eof_received."""
        client.eof_received()

    async def test_error_received(self, client):
        """Test error_received."""
        with pytest.raises(RuntimeError):
            client.error_received(Exception("test call"))

    async def test_callbacks(self, commparams):
        """Test callbacks."""
        client = Transport(commparams, False)
        client.callback_connected()
        client.callback_disconnected(Exception("test"))
        client.callback_data(b"abcd")

    async def test_transport_send(self, client):
        """Test transport_send()."""
        client.transport = mock.AsyncMock()
        client.transport_send(b"abc")

        client.comm_params.comm_type = CommType.UDP
        client.transport_send(b"abc")
        client.transport_send(b"abc", addr=("localhost", 502))

    async def test_transport_close(self, server, dummy_transport):
        """Test transport_close()."""
        dummy_transport.abort = mock.Mock()
        dummy_transport.close = mock.Mock()
        server.connection_made(dummy_transport)
        server.recv_buffer = b"abc"
        server.reconnect_task = mock.MagicMock()
        server.listener = mock.MagicMock()
        server.transport_close()
        dummy_transport.abort.assert_called_once()
        dummy_transport.close.assert_called_once()
        assert not server.recv_buffer
        assert not server.reconnect_task
        server.listener = None
        server.active_connections = {"a": dummy_transport}
        server.transport_close()
        assert not server.active_connections

    async def test_reset_delay(self, client, commparams):
        """Test reset_delay()."""
        client.reconnect_delay_current += 5.17
        client.reset_delay()
        assert client.reconnect_delay_current == commparams.reconnect_delay

    async def test_is_active(self, client):
        """Test is_active()."""
        assert not client.is_active()
        client.connection_made(mock.AsyncMock())
        assert client.is_active()

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    async def test_create_nullmodem(self, client, server):
        """Test create_nullmodem."""
        await server.transport_listen()
        await client.transport_listen()

    async def test_handle_new_connection(self, client, server):
        """Test handle_new_connection()."""
        server.handle_new_connection()
        client.handle_new_connection()

    async def test_do_reconnect(self, client):
        """Test do_reconnect()."""
        client.comm_params.reconnect_delay = 0.01
        client.transport_connect = mock.AsyncMock(side_effect=[False, True])
        await client.do_reconnect()
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay * 2
        assert not client.reconnect_task
        client.transport_connect.side_effect = asyncio.CancelledError("stop loop")
        await client.do_reconnect()
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay
        assert not client.reconnect_task

    async def test_with_magic(self, client):
        """Test magic."""
        client.transport_close = mock.MagicMock()
        async with client:
            pass
        client.transport_close.assert_called_once()

    async def test_str_magic(self, commparams, client):
        """Test magic."""
        assert str(client) == f"Transport({commparams.comm_name})"

    def test_generate_ssl(self, commparams):
        """Test ssl generattion"""
        with mock.patch("pymodbus.transport.transport.ssl.SSLContext"):
            sslctx = commparams.generate_ssl(True, "cert_file", "key_file")
        assert sslctx
        test_value = "test igen"
        assert test_value == commparams.generate_ssl(
            True, "cert_file", "key_file", sslctx=test_value
        )


class TestBasicNullModem:
    """Test transport null modem module."""

    def test_init(self):
        """Test null modem init"""
        NullModem.server = None
        with pytest.raises(OSError, match="Connect called before listen"):
            NullModem(False, mock.Mock())
        NullModem(True, mock.Mock())
        NullModem(False, mock.Mock())

    def test_external_methods(self):
        """Test external methods."""
        modem = NullModem(True, mock.Mock())
        modem.other = NullModem(False, mock.Mock())
        modem.other.protocol = mock.Mock()
        modem.sendto(b"abcd")
        modem.write(b"abcd")
        modem.close()

    async def test_serve_forever(self):
        """Test external methods."""
        modem = NullModem(True, mock.Mock())
        modem.serving.set_result(True)
        await modem.serve_forever()
        modem.close()

    def test_abstract_methods(self):
        """Test asyncio abstract methods."""
        modem = NullModem(True, mock.Mock())
        modem.abort()
        modem.can_write_eof()
        modem.get_write_buffer_size()
        modem.get_write_buffer_limits()
        modem.set_write_buffer_limits(1024, 1)
        modem.write_eof()
        modem.get_protocol()
        modem.set_protocol(None)
        modem.is_closing()
