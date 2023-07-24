"""Test transport."""
import asyncio
from unittest import mock

import pytest

from pymodbus.transport import (
    NULLMODEM_HOST,
    CommType,
    ModbusProtocol,
    NullModem,
)
from pymodbus.transport.transport_serial import (
    SerialTransport,
    create_serial_connection,
)


COMM_TYPES = [
    CommType.TCP,
    CommType.TLS,
    CommType.UDP,
    CommType.SERIAL,
]


class TestBasicModbusProtocol:
    """Test transport module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_my_port(base_ports):
        """Return next port"""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    def teardown(self):
        """Run class teardown"""
        assert not NullModem.is_dirty()

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
    @pytest.mark.parametrize("use_comm_type", COMM_TYPES)
    async def test_init_nullmodem(self, client, server):
        """Test init()"""
        client.comm_params.sslctx = None
        assert client.unique_id == str(id(client))
        assert not hasattr(client, "active_connections")
        assert not client.is_server
        assert not hasattr(server, "unique_id")
        assert not server.active_connections
        assert server.is_server

    @pytest.mark.parametrize(
        ("use_host", "use_comm_type"), [("socket://127.0.0.1:7001", CommType.SERIAL)]
    )
    async def test_init_serial(self, client, server):
        """Test init()"""
        assert client.unique_id == str(id(client))
        assert not client.is_server
        server.comm_params.sslctx = None
        assert server.is_server

    async def test_connect(self, client, dummy_protocol):
        """Test properties."""
        client.loop = None
        client.call_create = mock.AsyncMock(return_value=(dummy_protocol(), None))
        assert await client.transport_connect()
        assert client.loop
        client.call_create.side_effect = asyncio.TimeoutError("test")
        assert not await client.transport_connect()

    async def test_listen(self, server, dummy_protocol):
        """Test listen_tcp()."""
        server.call_create = mock.AsyncMock(return_value=(dummy_protocol(), None))
        server.loop = None
        assert await server.transport_listen()
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

    async def test_callbacks(self, use_clc):
        """Test callbacks."""
        client = ModbusProtocol(use_clc, False)
        client.callback_connected()
        client.callback_disconnected(Exception("test"))
        client.callback_data(b"abcd")

    async def test_transport_send(self, client):
        """Test transport_send()."""
        client.transport = mock.Mock()
        client.transport_send(b"abc")

        client.comm_params.comm_type = CommType.UDP
        client.transport_send(b"abc")
        client.transport_send(b"abc", addr=("localhost", 502))

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
        client.recv_buffer = b""
        client.transport_send(test_data)
        client.datagram_received(test_data, ("127.0.0.1", 502))
        assert not client.recv_buffer
        assert not client.sent_buffer
        client.datagram_received(test_data, ("127.0.0.1", 502))
        assert client.recv_buffer == test_data
        assert not client.sent_buffer
        client.transport_send(b"no echo")
        client.datagram_received(test_data, ("127.0.0.1", 502))
        assert client.recv_buffer == test_data + test_data
        assert not client.sent_buffer

    async def test_transport_close(self, server, dummy_protocol):
        """Test transport_close()."""
        dummy_protocol.abort = mock.MagicMock()
        dummy_protocol.close = mock.MagicMock()
        server.connection_made(dummy_protocol())
        server.recv_buffer = b"abc"
        server.reconnect_task = mock.MagicMock()
        server.transport_close()
        dummy_protocol.abort.assert_called_once()
        dummy_protocol.close.assert_called_once()
        assert not server.recv_buffer
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

    @pytest.mark.parametrize("use_host", [NULLMODEM_HOST])
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

    def test_generate_ssl(self, use_clc):
        """Test ssl generattion"""
        with mock.patch("pymodbus.transport.transport.ssl.SSLContext"):
            sslctx = use_clc.generate_ssl(True, "cert_file", "key_file")
        assert sslctx
        test_value = "test igen"
        assert test_value == use_clc.generate_ssl(
            True, "cert_file", "key_file", sslctx=test_value
        )


class TestBasicSerial:
    """Test transport serial module."""

    @staticmethod
    @pytest.fixture(name="use_port")
    def get_my_port(base_ports):
        """Return next port"""
        base_ports[__class__.__name__] += 1
        return base_ports[__class__.__name__]

    @mock.patch(
        "pymodbus.transport.transport_serial.serial.serial_for_url", mock.Mock()
    )
    async def test_init(self):
        """Test null modem init"""
        SerialTransport(asyncio.get_running_loop(), mock.Mock(), "dummy")

    @mock.patch(
        "pymodbus.transport.transport_serial.serial.serial_for_url", mock.Mock()
    )
    async def test_abstract_methods(self):
        """Test asyncio abstract methods."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), "dummy")
        assert comm.loop
        comm.get_protocol()
        comm.set_protocol(None)
        comm.get_write_buffer_limits()
        comm.can_write_eof()
        comm.write_eof()
        comm.set_write_buffer_limits(1024, 1)
        comm.get_write_buffer_size()
        comm.is_reading()
        comm.pause_reading()
        comm.resume_reading()
        comm.is_closing()

    @mock.patch(
        "pymodbus.transport.transport_serial.serial.serial_for_url", mock.Mock()
    )
    async def xtest_external_methods(self):
        """Test external methods."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), "dummy")
        comm.write(b"abcd")
        comm.flush()
        comm.close()
        comm.abort()
        assert await create_serial_connection(
            asyncio.get_running_loop(), mock.Mock, url="dummy"
        )

    async def test_serve_forever(self):
        """Test external methods."""
        modem = NullModem(mock.Mock())
        modem.serving.set_result(True)
        await modem.serve_forever()
        modem.close()
