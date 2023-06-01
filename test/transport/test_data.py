"""Test transport."""
import asyncio

import pytest

from pymodbus.framer import ModbusFramer, ModbusSocketFramer
from pymodbus.transport.transport import BaseTransport


class TestDataTransport:
    """Test for the transport module."""

    class dummy_transport(BaseTransport):
        """Transport class for test."""

        def cb_connection_made(self):
            """Handle callback."""

        def cb_connection_lost(self, _exc):
            """Handle callback."""

        def cb_handle_data(self, _data):
            """Handle callback."""
            return 0

        def __init__(self, framer: ModbusFramer, comm_name="test comm"):
            """Initialize."""
            super().__init__(
                comm_name,
                [2500, 9000],
                2000,
                framer,
                self.cb_connection_made,
                self.cb_connection_lost,
                self.cb_handle_data,
            )

    @pytest.mark.skipif(pytest.IS_WINDOWS, reason="Windows problem.")
    @pytest.mark.xdist_group(name="server_serialize")
    async def test_client_send(self):
        """Test connect() reconnecting."""
        server = self.dummy_transport(ModbusSocketFramer, comm_name="server mode")
        server.setup_tcp(True, "localhost", 5101)
        await server.transport_listen()
        assert server.transport

        client = self.dummy_transport(ModbusSocketFramer, comm_name="client mode")
        client.setup_tcp(False, "localhost", 5101)
        assert await client.transport_connect() != (None, None)
        await client.send(b"ABC")
        await asyncio.sleep(2)
        assert server.recv_buffer == b"ABC"
        await server.send(b"DEF")
        await asyncio.sleep(2)
        assert client.recv_buffer == b"DEF"
