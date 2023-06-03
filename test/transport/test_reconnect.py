"""Test transport."""
import asyncio
from unittest import mock

from pymodbus.framer import ModbusFramer
from pymodbus.transport.transport import BaseTransport


class TestBaseTransport:
    """Test transport module, base part."""

    base_comm_name = "test comm"
    base_reconnect_delay = 1.0
    base_reconnect_delay_max = 7.5
    base_timeout_connect = 2.0
    base_framer = ModbusFramer
    base_host = "test host"
    base_port = 502
    base_server_hostname = "server test host"
    base_baudrate = 9600
    base_bytesize = 8
    base_parity = "e"
    base_stopbits = 2

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
        return base, params

    async def test_no_reconnect_call(self):
        """Test connection_lost()."""
        transport, _params = await self.setup_BaseTransport()
        transport.setup_tcp(False, self.base_host, self.base_port)
        transport.call_connect_listen = mock.AsyncMock(return_value=(None, None))
        transport.connection_made(mock.Mock())
        assert not transport.call_connect_listen.call_count
        assert transport.reconnect_delay_current == self.base_reconnect_delay

        transport.connection_lost(RuntimeError("Connection lost"))
        assert not transport.call_connect_listen.call_count
        assert transport.reconnect_delay_current == self.base_reconnect_delay
        transport.close()

    async def test_reconnect_call(self):
        """Test connection_lost()."""
        transport, _params = await self.setup_BaseTransport()
        transport.setup_tcp(False, self.base_host, self.base_port)
        transport.call_connect_listen = mock.AsyncMock(return_value=(None, None))
        transport.connection_made(mock.Mock())
        transport.connection_lost(RuntimeError("Connection lost"))

        await asyncio.sleep(transport.reconnect_delay_current * 1.2)
        assert transport.call_connect_listen.call_count == 1
        assert transport.reconnect_delay_current == self.base_reconnect_delay * 2
        transport.close()

    async def test_multi_reconnect_call(self):
        """Test connection_lost()."""
        transport, _params = await self.setup_BaseTransport()
        transport.setup_tcp(False, self.base_host, self.base_port)
        transport.call_connect_listen = mock.AsyncMock(return_value=(None, None))
        transport.connection_made(mock.Mock())
        transport.connection_lost(RuntimeError("Connection lost"))

        await asyncio.sleep(transport.reconnect_delay_current * 1.2)
        assert transport.call_connect_listen.call_count == 1
        assert transport.reconnect_delay_current == self.base_reconnect_delay * 2

        await asyncio.sleep(transport.reconnect_delay_current * 1.2)
        assert transport.call_connect_listen.call_count == 2
        assert transport.reconnect_delay_current == self.base_reconnect_delay * 4

        await asyncio.sleep(transport.reconnect_delay_current * 1.2)
        assert transport.call_connect_listen.call_count == 3
        assert transport.reconnect_delay_current == self.base_reconnect_delay_max
        transport.close()

    async def test_reconnect_call_ok(self):
        """Test connection_lost()."""
        transport, _params = await self.setup_BaseTransport()
        transport.setup_tcp(False, self.base_host, self.base_port)
        transport.call_connect_listen = mock.AsyncMock(
            return_value=(mock.Mock(), mock.Mock())
        )
        transport.connection_made(mock.Mock())
        transport.connection_lost(RuntimeError("Connection lost"))

        await asyncio.sleep(transport.reconnect_delay_current * 1.2)
        assert transport.call_connect_listen.call_count == 1
        assert transport.reconnect_delay_current == self.base_reconnect_delay * 2
        assert not transport.reconnect_timer
        transport.close()
