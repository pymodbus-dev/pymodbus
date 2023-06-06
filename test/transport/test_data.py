"""Test transport."""
import asyncio


BASE_PORT = 5240


class TestDataTransport:  # pylint: disable=too-few-public-methods
    """Test for the transport module."""

    async def test_client_send(self, transport, transport_server):
        """Test send()."""
        transport_server.setup_tcp(True, "localhost", BASE_PORT + 1)
        server = await transport_server.transport_listen()
        assert transport_server.transport

        transport.setup_tcp(False, "localhost", BASE_PORT + 1)
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
