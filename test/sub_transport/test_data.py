"""Test transport."""
import asyncio

import pytest


class TestDataTransport:  # pylint: disable=too-few-public-methods
    """Test for the transport module."""

    @pytest.mark.xdist_group(name="server_serialize")
    async def test_client_send(self, transport, transport_server, use_port):
        """Test send()."""
        transport_server.setup_tcp(True, "localhost", use_port)
        server = await transport_server.transport_listen()
        assert transport_server.transport

        transport.setup_tcp(False, "localhost", use_port)
        assert await transport.transport_connect()
        await transport.send(b"ABC")
        await asyncio.sleep(2)
        assert transport_server.recv_buffer == b"ABC"
        await transport_server.send(b"DEF")
        await asyncio.sleep(2)
        assert transport.recv_buffer == b"DEF"
        transport.close()
        transport_server.close()
        server.close()
