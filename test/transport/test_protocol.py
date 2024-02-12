"""Test transport."""
import asyncio
from unittest import mock

import pytest

from pymodbus.transport import (
    CommType,
    ModbusProtocol,
)


COMM_TYPES = [
    CommType.TCP,
    CommType.TLS,
    CommType.UDP,
    CommType.SERIAL,
]


class TestTransportProtocol1:
    """Test transport module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port."""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]


    @pytest.mark.parametrize("use_comm_type", COMM_TYPES)
    async def test_init_client(self, client):
        """Test init client."""
        assert not hasattr(client, "active_connections")
        assert not client.is_server


    @pytest.mark.parametrize("use_comm_type", COMM_TYPES)
    async def test_init_server(self, server):
        """Test init server."""
        assert not hasattr(server, "unique_id")
        assert not server.active_connections
        assert server.is_server

    @pytest.mark.parametrize("use_comm_type", COMM_TYPES)
    async def test_init_client_id(self, client):
        """Test init client id."""
        assert client.unique_id == str(id(client))

    async def test_init_source_addr(self, use_clc):
        """Test callbacks."""
        use_clc.source_address = ("localhost", 112)
        ModbusProtocol(use_clc, True)

    async def test_init_source_addr_none(self, use_clc):
        """Test callbacks."""
        use_clc.source_address = None
        ModbusProtocol(use_clc, True)

    async def test_loop_connect(self, client, dummy_protocol):
        """Test properties."""
        client.loop = None
        client.call_create = mock.AsyncMock(return_value=(dummy_protocol(), None))
        assert await client.transport_connect()
        assert client.loop

    async def test_loop_listen(self, server, dummy_protocol):
        """Test properties."""
        server.call_create = mock.AsyncMock(return_value=(dummy_protocol(), None))
        server.loop = asyncio.get_running_loop()
        assert await server.transport_listen()
        assert server.loop

    async def test_connect_ok(self, client, dummy_protocol):
        """Test properties."""
        client.call_create = mock.AsyncMock(return_value=(dummy_protocol(), None))
        assert await client.transport_connect()

    async def test_connect_not_ok(self, client, dummy_protocol):
        """Test properties."""
        client.call_create = mock.AsyncMock(return_value=(dummy_protocol(), None))
        client.call_create.side_effect = asyncio.TimeoutError("test")
        assert not await client.transport_connect()

    async def test_listen_ok(self, server, dummy_protocol):
        """Test listen_tcp()."""
        server.call_create = mock.AsyncMock(return_value=(dummy_protocol(), None))
        assert await server.transport_listen()

    async def test_listen_not_ok(self, server, dummy_protocol):
        """Test listen_tcp()."""
        server.call_create = mock.AsyncMock(return_value=(dummy_protocol(), None))
        server.call_create.side_effect = OSError("testing")
        assert not await server.transport_listen()

    async def test_connection_made(self, client, use_clc, dummy_protocol):
        """Test connection_made()."""
        client.connection_made(dummy_protocol())
        assert client.transport
        assert not client.recv_buffer
        assert not client.reconnect_task
        assert client.reconnect_delay_current == use_clc.reconnect_delay
        client.callback_connected.assert_called_once()

    async def test_connection_lost(self, client, dummy_protocol):
        """Test connection_lost()."""
        client.connection_lost(RuntimeError("not implemented"))
        client.connection_made(dummy_protocol())
        client.connection_lost(RuntimeError("not implemented"))
        assert not client.transport
        assert not client.recv_buffer
        assert client.reconnect_task
        client.callback_disconnected.assert_called_once()
        client.transport_close()
        assert not client.reconnect_task
        assert not client.reconnect_delay_current

    async def test_data_received_rest(self, client):
        """Test data_received."""
        client.callback_data = mock.MagicMock(return_value=2)
        client.data_received(b"123456")
        client.callback_data.assert_called_once()
        assert client.recv_buffer == b"3456"
        client.data_received(b"789")
        assert client.recv_buffer == b"56789"

    async def test_data_received_all(self, client):
        """Test data_received."""
        test_data = b"123"
        client.callback_data = mock.MagicMock(return_value=len(test_data))
        client.data_received(test_data)
        assert not client.recv_buffer

    async def test_datagram(self, client):
        """Test datagram_received()."""
        client.callback_data = mock.MagicMock()
        client.datagram_received(b"abc", "127.0.0.1")
        client.callback_data.assert_called_once()

    async def test_callback_connected(self, use_clc):
        """Test callbacks."""
        client = ModbusProtocol(use_clc, False)
        client.callback_connected()

    async def test_callback_disconnected(self, use_clc):
        """Test callbacks."""
        client = ModbusProtocol(use_clc, False)
        client.callback_disconnected(Exception("test"))

    async def test_callback_data(self, use_clc):
        """Test callbacks."""
        client = ModbusProtocol(use_clc, False)
        client.callback_data(b"abcd")

    async def test_handle_local_echo(self, client):
        """Test transport_send()."""
        client.comm_params.handle_local_echo = True
        client.transport = mock.Mock()
        test_data = b"abc"
        client.transport_send(test_data)
        client.data_received(test_data)
        assert not client.recv_buffer
        client.data_received(test_data)
        assert client.recv_buffer == test_data
        assert not client.sent_buffer

    async def test_handle_local_echo_udp(self, client):
        """Test transport_send()."""
        client.comm_params.handle_local_echo = True
        client.transport = mock.Mock()
        test_data = b"abc"
        client.transport_send(test_data)
        client.datagram_received(test_data, ("127.0.0.1", 502))
        assert not client.recv_buffer
        assert not client.sent_buffer
        client.datagram_received(test_data, ("127.0.0.1", 502))
        assert client.recv_buffer == test_data
        assert not client.sent_buffer

    async def test_handle_local_echo_none(self, client):
        """Test transport_send()."""
        client.comm_params.handle_local_echo = True
        client.transport = mock.Mock()
        test_data = b"abc"
        client.transport_send(b"no echo")
        client.datagram_received(test_data, ("127.0.0.1", 502))
        assert client.recv_buffer == test_data
        assert not client.sent_buffer

    async def test_handle_local_echo_partial(self, client):
        """Test transport_send()."""
        client.comm_params.handle_local_echo = True
        client.transport = mock.Mock()
        client.transport_send(b"partial")
        client.datagram_received(b"par", ("127.0.0.1", 502))
        client.datagram_received(b"tialresponse", ("127.0.0.1", 502))
        assert client.recv_buffer == b"response"
        assert not client.sent_buffer


class TestTransportProtocol2:
    """Test transport module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_port_in_class(base_ports):
        """Return next port."""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]


    async def test_eof_received(self, client):
        """Test eof_received."""
        client.eof_received()

    async def test_error_received(self, client):
        """Test error_received."""
        client.error_received(Exception("test call"))

    async def test_transport_send(self, client):
        """Test transport_send()."""
        client.transport = mock.Mock()
        client.transport_send(b"abc")

    async def test_transport_send_udp(self, client):
        """Test transport_send()."""
        client.transport = mock.Mock()
        client.comm_params.comm_type = CommType.UDP
        client.transport_send(b"abc", addr=("localhost", 502))

    async def test_transport_send_udp_no_addr(self, client):
        """Test transport_send()."""
        client.transport = mock.Mock()
        client.comm_params.comm_type = CommType.UDP
        client.transport_send(b"abc")

    async def test_transport_close_connection(self, server, dummy_protocol):
        """Test transport_close()."""
        dummy_protocol.close = mock.MagicMock()
        server.connection_made(dummy_protocol())
        server.recv_buffer = b"abc"
        server.reconnect_task = mock.MagicMock()
        server.transport_close()
        dummy_protocol.close.assert_called_once()
        assert not server.recv_buffer

    async def test_transport_close_listen(self, server, dummy_protocol):
        """Test transport_close()."""
        dummy_protocol.close = mock.MagicMock()
        await server.transport_listen()
        server.active_connections = {"a": dummy_protocol()}
        server.transport_close()
        server.transport_close()
        assert not server.active_connections

    async def test_transport_close2(self, server, client, dummy_protocol):
        """Test transport_close()."""
        dummy_protocol.abort = mock.Mock()
        dummy_protocol.close = mock.Mock()
        client.connection_made(dummy_protocol())
        client.recv_buffer = b"abc"
        client.reconnect_task = mock.MagicMock()
        client.listener = server
        server.active_connections = {client.unique_id: dummy_protocol}
        client.transport_close()
        assert not server.active_connections

    async def test_reset_delay(self, client, use_clc):
        """Test reset_delay()."""
        client.reconnect_delay_current += 5.17
        client.reset_delay()
        assert client.reconnect_delay_current == use_clc.reconnect_delay

    async def test_is_active(self, client):
        """Test is_active()."""
        assert not client.is_active()
        client.connection_made(mock.Mock())
        assert client.is_active()
        client.transport_close()

    async def test_create_nullmodem(self, client, server):
        """Test create_nullmodem."""
        assert not await client.transport_connect()
        await server.transport_listen()
        assert await client.transport_connect()
        client.transport_close()
        server.transport_close()

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
        client.comm_params.on_reconnect_callback = mock.Mock()
        await client.do_reconnect()
        assert client.reconnect_delay_current == client.comm_params.reconnect_delay
        assert not client.reconnect_task

    async def test_with_magic(self, client):
        """Test magic."""
        client.transport_close = mock.MagicMock()
        async with client:
            pass
        client.transport_close.assert_called_once()

    async def test_str_magic(self, use_clc, client):
        """Test magic."""
        assert str(client) == f"ModbusProtocol({use_clc.comm_name})"

    def test_generate_ssl_cert(self, use_clc):
        """Test ssl generation."""
        with mock.patch("pymodbus.transport.transport.ssl.SSLContext"):
            sslctx = use_clc.generate_ssl(True, "cert_file", "key_file")
        assert sslctx

    def test_generate_ssl_ctx(self, use_clc):
        """Test ssl generation."""
        test_value = "test igen"
        assert test_value == use_clc.generate_ssl(
            True, "cert_file", "key_file", sslctx=test_value
        )

    def test_generate_ssl_client(self, use_clc):
        """Test ssl generation."""
        test_value = "test igen"
        assert test_value == use_clc.generate_ssl(
            False, "cert_file", "key_file", sslctx=test_value
        )

    def test_generate_ssl_no_file(self, use_clc):
        """Test ssl generation."""
        assert use_clc.generate_ssl(True, None, None)

    @pytest.mark.parametrize("use_host", ["socket://localhost:5005", "/dev/tty"])
    @pytest.mark.parametrize("use_comm_type", [CommType.SERIAL])
    def test_init_serial(self, use_cls):
        """Test server serial with socket."""
        ModbusProtocol(use_cls, True)

    @pytest.mark.parametrize("use_host", ["socket://localhost:5006"])
    @pytest.mark.parametrize("use_comm_type", [CommType.SERIAL])
    async def test_init_create_serial(self, use_cls):
        """Test server serial with socket."""
        protocol = ModbusProtocol(use_cls, True)
        await protocol.transport_listen()

    @pytest.mark.parametrize("use_host", ["localhost"])
    @pytest.mark.parametrize("use_comm_type", [CommType.UDP])
    @pytest.mark.parametrize("is_server", [True, False])
    def test_init_udp(self, is_server, use_cls, use_clc):
        """Test server/client udp."""
        if is_server:
            ModbusProtocol(use_cls, True)
        else:
            ModbusProtocol(use_clc, False)
