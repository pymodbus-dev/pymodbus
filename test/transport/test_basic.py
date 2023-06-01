"""Test transport."""
import asyncio
import os
from unittest import mock

import pytest
from serial import SerialException

from pymodbus.framer import ModbusFramer
from pymodbus.transport.transport import BaseTransport


class TestBaseTransport:
    """Test transport module, base part."""

    base_comm_name = "test comm"
    base_reconnect_delay = 1
    base_reconnect_delay_max = 3.5
    base_timeout_connect = 2
    base_framer = ModbusFramer
    base_host = "test host"
    base_port = 502
    base_server_hostname = "server test host"
    base_baudrate = 9600
    base_bytesize = 8
    base_parity = "e"
    base_stopbits = 2
    cwd = None

    class dummy_transport(BaseTransport):
        """Transport class for test."""

        def __init__(self):
            """Initialize."""
            super().__init__(
                TestBaseTransport.base_comm_name,
                [
                    TestBaseTransport.base_reconnect_delay * 1000,
                    TestBaseTransport.base_reconnect_delay_max * 1000,
                ],
                TestBaseTransport.base_timeout_connect * 1000,
                TestBaseTransport.base_framer,
                None,
                None,
                None,
            )
            self.abort = mock.MagicMock()
            self.close = mock.MagicMock()

    @classmethod
    async def setup_BaseTransport(cls):
        """Create base object."""
        base = BaseTransport(
            cls.base_comm_name,
            (cls.base_reconnect_delay * 1000, cls.base_reconnect_delay_max * 1000),
            cls.base_timeout_connect * 1000,
            cls.base_framer,
            mock.MagicMock(),
            mock.MagicMock(),
            mock.MagicMock(),
        )
        params = base.CommParamsClass(
            done=True,
            comm_name=cls.base_comm_name,
            reconnect_delay=cls.base_reconnect_delay,
            reconnect_delay_max=cls.base_reconnect_delay_max,
            timeout_connect=cls.base_timeout_connect,
            framer=cls.base_framer,
        )
        cls.cwd = os.getcwd().split("/")[-1]
        if cls.cwd == "transport":
            cls.cwd = "../../"
        elif cls.cwd == "test":
            cls.cwd = "../"
        else:
            cls.cwd = ""
        cls.cwd = cls.cwd + "examples/certificates/pymodbus."
        return base, params

    async def test_init(self):
        """Test init()"""
        base, params = await self.setup_BaseTransport()
        params.done = False
        assert base.comm_params == params

        assert base.cb_connection_made
        assert base.cb_connection_lost
        assert base.cb_handle_data
        assert not base.reconnect_delay_current
        assert not base.reconnect_timer

    async def test_property_done(self):
        """Test done property"""
        base, params = await self.setup_BaseTransport()
        base.comm_params.check_done()
        with pytest.raises(RuntimeError):
            base.comm_params.check_done()

    @pytest.mark.skipif(
        pytest.IS_WINDOWS, reason="Windows do not support unix sockets."
    )
    @pytest.mark.parametrize("setup_server", [True, False])
    async def test_properties_unix(self, setup_server):
        """Test properties."""
        base, params = await self.setup_BaseTransport()
        base.setup_unix(setup_server, self.base_host)
        params.host = self.base_host
        assert base.comm_params == params
        assert base.call_connect_listen

    @pytest.mark.skipif(
        not pytest.IS_WINDOWS, reason="Windows do not support unix sockets."
    )
    @pytest.mark.parametrize("setup_server", [True, False])
    async def test_properties_unix_windows(self, setup_server):
        """Test properties."""
        base, params = await self.setup_BaseTransport()
        with pytest.raises(RuntimeError):
            base.setup_unix(setup_server, self.base_host)

    @pytest.mark.parametrize("setup_server", [True, False])
    async def test_properties_tcp(self, setup_server):
        """Test properties."""
        base, params = await self.setup_BaseTransport()
        base.setup_tcp(setup_server, self.base_host, self.base_port)
        params.host = self.base_host
        params.port = self.base_port
        assert base.comm_params == params
        assert base.call_connect_listen

    @pytest.mark.parametrize("setup_server", [True, False])
    async def test_properties_udp(self, setup_server):
        """Test properties."""
        base, params = await self.setup_BaseTransport()
        base.setup_udp(setup_server, self.base_host, self.base_port)
        params.host = self.base_host
        params.port = self.base_port
        assert base.comm_params == params
        assert base.call_connect_listen

    @pytest.mark.parametrize("setup_server", [True, False])
    @pytest.mark.parametrize("sslctx", [None, "test ctx"])
    async def test_properties_tls(self, setup_server, sslctx):
        """Test properties."""
        base, params = await self.setup_BaseTransport()
        with mock.patch("pymodbus.transport.transport.ssl.SSLContext"):
            base.setup_tls(
                setup_server,
                self.base_host,
                self.base_port,
                sslctx,
                None,
                None,
                None,
                self.base_server_hostname,
            )
            params.host = self.base_host
            params.port = self.base_port
            params.server_hostname = self.base_server_hostname
            params.ssl = sslctx if sslctx else base.comm_params.ssl
            assert base.comm_params == params
            assert base.call_connect_listen

    @pytest.mark.parametrize("setup_server", [True, False])
    async def test_properties_serial(self, setup_server):
        """Test properties."""
        base, params = await self.setup_BaseTransport()
        base.setup_serial(
            setup_server,
            self.base_host,
            self.base_baudrate,
            self.base_bytesize,
            self.base_parity,
            self.base_stopbits,
        )
        params.host = self.base_host
        params.baudrate = self.base_baudrate
        params.bytesize = self.base_bytesize
        params.parity = self.base_parity
        params.stopbits = self.base_stopbits
        assert base.comm_params == params
        assert base.call_connect_listen

    async def test_with_magic(self):
        """Test magic."""
        base, _params = await self.setup_BaseTransport()
        base.close = mock.MagicMock()
        async with base:
            pass
        base.close.assert_called_once()

    async def test_str_magic(self):
        """Test magic."""
        base, _params = await self.setup_BaseTransport()
        assert str(base) == f"BaseTransport({self.base_comm_name})"

    async def test_connection_made(self):
        """Test connection_made()."""
        base, params = await self.setup_BaseTransport()
        transport = self.dummy_transport()
        base.connection_made(transport)
        assert base.transport == transport
        assert not base.recv_buffer
        assert not base.reconnect_timer
        assert base.reconnect_delay_current == params.reconnect_delay
        base.cb_connection_made.assert_called_once()
        base.cb_connection_lost.assert_not_called()
        base.cb_handle_data.assert_not_called()
        base.close()

    async def test_connection_lost(self):
        """Test connection_lost()."""
        base, params = await self.setup_BaseTransport()
        transport = self.dummy_transport()
        base.connection_lost(transport)
        assert not base.transport
        assert not base.recv_buffer
        assert not base.reconnect_timer
        assert not base.reconnect_delay_current
        base.cb_connection_made.assert_not_called()
        base.cb_handle_data.assert_not_called()
        base.cb_connection_lost.assert_called_once()
        # reconnect is only after a successful connect
        base.connection_made(transport)
        base.connection_lost(transport)
        assert base.reconnect_timer
        assert not base.transport
        assert not base.recv_buffer
        assert base.reconnect_timer
        assert base.reconnect_delay_current == 2 * params.reconnect_delay
        base.cb_connection_lost.call_count == 2
        base.close()
        assert not base.reconnect_timer

    async def test_eof_received(self):
        """Test connection_lost()."""
        base, params = await self.setup_BaseTransport()
        self.dummy_transport()
        base.eof_received()
        assert not base.transport
        assert not base.recv_buffer
        assert not base.reconnect_timer
        assert not base.reconnect_delay_current

    async def test_close(self):
        """Test close()."""
        base, _params = await self.setup_BaseTransport()
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

    async def test_reset_delay(self):
        """Test reset_delay()."""
        base, _params = await self.setup_BaseTransport()
        base.reconnect_delay_current = self.base_reconnect_delay + 1
        base.reset_delay()
        assert base.reconnect_delay_current == self.base_reconnect_delay

    async def test_datagram(self):
        """Test datagram_received()."""
        base, _params = await self.setup_BaseTransport()
        base.data_received = mock.MagicMock()
        base.datagram_received(b"abc", "127.0.0.1")
        base.data_received.assert_called_once()

    async def test_data(self):
        """Test data_received."""
        base, _params = await self.setup_BaseTransport()
        base.cb_handle_data = mock.MagicMock(return_value=2)
        base.data_received(b"123456")
        base.cb_handle_data.assert_called_once()
        assert base.recv_buffer == b"3456"
        base.data_received(b"789")
        assert base.recv_buffer == b"56789"

    async def test_send(self):
        """Test send()."""
        base, _params = await self.setup_BaseTransport()
        base.transport = mock.AsyncMock()
        await base.send(b"abc")

    @pytest.mark.skipif(
        pytest.IS_WINDOWS, reason="Windows do not support unix sockets."
    )
    async def test_connect_unix(self):
        """Test connect_unix()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_unix(False, self.base_host)
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        base.loop.create_unix_connection = mocker
        mocker.side_effect = FileNotFoundError("testing")
        assert await base.transport_connect() == (None, None)
        base.close.assert_called_once()
        mocker.side_effect = None

        mocker.return_value = (117, 118)
        assert mocker.return_value == await base.transport_connect()
        base.close.called_once()

    async def test_connect_tcp(self):
        """Test connect_tcp()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_tcp(False, self.base_host, self.base_port)
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        base.loop.create_connection = mocker
        mocker.side_effect = asyncio.TimeoutError("testing")
        assert await base.transport_connect() == (None, None)
        base.close.assert_called_once()
        mocker.side_effect = None

        mocker.return_value = (117, 118)
        assert mocker.return_value == await base.transport_connect()
        base.close.assert_called_once()

    async def test_connect_tls(self):
        """Test connect_tcls()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_tls(
            False,
            self.base_host,
            self.base_port,
            "no ssl",
            None,
            None,
            None,
            self.base_server_hostname,
        )
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        base.loop.create_connection = mocker
        mocker.side_effect = asyncio.TimeoutError("testing")
        assert await base.transport_connect() == (None, None)
        base.close.assert_called_once()
        mocker.side_effect = None

        mocker.return_value = (117, 118)
        assert mocker.return_value == await base.transport_connect()
        base.close.assert_called_once()

    async def test_connect_udp(self):
        """Test connect_udp()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_udp(False, self.base_host, self.base_port)
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        base.loop.create_datagram_endpoint = mocker
        mocker.side_effect = asyncio.TimeoutError("testing")
        assert await base.transport_connect() == (None, None)
        base.close.assert_called_once()
        mocker.side_effect = None

        mocker.return_value = (117, 118)
        assert mocker.return_value == await base.transport_connect()
        base.close.assert_called_once()

    async def test_connect_serial(self):
        """Test connect_serial()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_serial(
            False,
            self.base_host,
            self.base_baudrate,
            self.base_bytesize,
            self.base_parity,
            self.base_stopbits,
        )
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        with mock.patch(
            "pymodbus.transport.transport.create_serial_connection", new=mocker
        ):
            mocker.side_effect = asyncio.TimeoutError("testing")
            assert await base.transport_connect() == (None, None)
            base.close.assert_called_once()
            mocker.side_effect = None

            mocker.return_value = (117, 118)
            assert mocker.return_value == await base.transport_connect()
            base.close.assert_called_once()

    @pytest.mark.skipif(
        pytest.IS_WINDOWS, reason="Windows do not support unix sockets."
    )
    async def test_listen_unix(self):
        """Test listen_unix()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_unix(True, self.base_host)
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        base.loop.create_unix_server = mocker
        mocker.side_effect = OSError("testing")
        assert await base.transport_listen() is None
        base.close.assert_called_once()
        mocker.side_effect = None

        mocker.return_value = 117
        assert mocker.return_value == await base.transport_listen()
        base.close.assert_called_once()

    async def test_listen_tcp(self):
        """Test listen_tcp()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_tcp(True, self.base_host, self.base_port)
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        base.loop.create_server = mocker
        mocker.side_effect = OSError("testing")
        assert await base.transport_listen() is None
        base.close.assert_called_once()
        mocker.side_effect = None

        mocker.return_value = 117
        assert mocker.return_value == await base.transport_listen()
        base.close.assert_called_once()

    async def test_listen_tls(self):
        """Test listen_tls()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_tls(
            True,
            self.base_host,
            self.base_port,
            "no ssl",
            None,
            None,
            None,
            self.base_server_hostname,
        )
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        base.loop.create_server = mocker
        mocker.side_effect = OSError("testing")
        assert await base.transport_listen() is None
        base.close.assert_called_once()
        mocker.side_effect = None

        mocker.return_value = 117
        assert mocker.return_value == await base.transport_listen()
        base.close.assert_called_once()

    async def test_listen_udp(self):
        """Test listen_udp()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_udp(True, self.base_host, self.base_port)
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        base.loop.create_datagram_endpoint = mocker
        mocker.side_effect = OSError("testing")
        assert await base.transport_listen() is None
        base.close.assert_called_once()
        mocker.side_effect = None

        mocker.return_value = (117, 118)
        assert await base.transport_listen() == 117
        base.close.assert_called_once()

    async def test_listen_serial(self):
        """Test listen_serial()."""
        base, _params = await self.setup_BaseTransport()
        base.setup_serial(
            True,
            self.base_host,
            self.base_baudrate,
            self.base_bytesize,
            self.base_parity,
            self.base_stopbits,
        )
        base.close = mock.Mock()
        mocker = mock.AsyncMock()

        with mock.patch(
            "pymodbus.transport.transport.create_serial_connection", new=mocker
        ):
            mocker.side_effect = SerialException("testing")
            assert await base.transport_listen() is None
            base.close.assert_called_once()
            mocker.side_effect = None

            mocker.return_value = 117
            assert await base.transport_listen() == 117
            base.close.assert_called_once()
