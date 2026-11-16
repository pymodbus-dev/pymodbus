"""Test the sync tcp client, that runs the async client on a private loop.

The server runs on the test loop, so the sync client is called from another
thread with asyncio.to_thread().
"""

import asyncio
import threading
from unittest import mock

import pytest

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.framer import FramerType


def client_threads() -> list[threading.Thread]:
    """Return the threads of the private loops."""
    return [t for t in threading.enumerate() if t.name == "pymodbus-sync-client"]


@pytest.mark.parametrize("use_host", ["localhost"])
@pytest.mark.parametrize(("use_comm", "use_framer"), [("tcp", "socket")])
class TestSyncClientLoop:
    """Test the sync tcp client."""

    @pytest.fixture(name="use_port")
    @staticmethod
    def get_port_in_class(base_ports):
        """Return next port."""
        base_ports[__class__.__name__] += 1  # type: ignore[index, name-defined]
        return base_ports[__class__.__name__]  # type: ignore[index, name-defined]

    @pytest.fixture(name="client")
    @staticmethod
    def define_client(use_comm, use_framer, use_host, use_port):
        """Return a sync tcp client."""
        assert use_comm == "tcp"
        client = ModbusTcpClient(
            use_host, framer=FramerType(use_framer), port=use_port, timeout=1
        )
        yield client
        client.close()

    @pytest.mark.parametrize("run_async", [True, False])
    async def test_read(self, mock_server, client, run_async):
        """Test requests with the async counterpart and with the sync code."""
        assert mock_server

        def run():
            assert client.connect()
            for _ in range(3):
                assert client.read_holding_registers(0, count=10).registers == [17] * 10
            assert len(client_threads()) == (1 if run_async else 0)
            client.close()
            assert not client.connected

        with mock.patch.object(ModbusTcpClient, "_run_async", run_async):
            await asyncio.to_thread(run)
        assert not client_threads()

    async def test_connect_on_request(self, mock_server, client):
        """Test that a request connects, and connects again after close."""
        assert mock_server

        def run():
            assert client.read_holding_registers(0, count=1).registers == [17]
            client.close()
            assert client.read_holding_registers(0, count=1).registers == [17]
            client.close()

        await asyncio.to_thread(run)
        assert not client_threads()

    async def test_with(self, mock_server, use_host, use_port):
        """Test the with block."""
        assert mock_server

        def run():
            with ModbusTcpClient(use_host, port=use_port) as client:
                assert client.read_holding_registers(0, count=1).registers == [17]
            assert not client.connected

        await asyncio.to_thread(run)
        assert not client_threads()

    def test_connect_fails(self, client):
        """Test that a failed connect does not leave the private loop running."""
        assert not client.connect()
        assert not client_threads()
        with pytest.raises(ConnectionException):
            client.read_holding_registers(0, count=1)
        assert not client_threads()

    async def test_exception(self, mock_server, client):
        """Test that an exception in the async client reaches the app."""
        assert mock_server

        def run():
            assert client.connect()
            async_client = client._async_client  # pylint: disable=protected-access
            assert async_client
            error = ModbusIOException("raised on the private loop")
            with (
                mock.patch.object(async_client, "execute", side_effect=error),
                pytest.raises(ModbusIOException) as exc,
            ):
                client.read_holding_registers(0, count=1)
            assert exc.value is error
            # The client is still usable after the exception.
            assert client.read_holding_registers(0, count=1).registers == [17]

        await asyncio.to_thread(run)

    async def test_in_running_loop(self, mock_server, client):
        """Test the sync client, called from a thread that runs a loop."""
        assert mock_server

        async def read_in_loop():
            return client.read_holding_registers(0, count=1).registers

        assert await asyncio.to_thread(asyncio.run, read_in_loop()) == [17]

    async def test_set_max_no_responses(self, mock_server, client):
        """Test that the setting reaches the async client."""
        assert mock_server

        def run():
            client.set_max_no_responses(7)
            assert client.connect()
            async_client = client._async_client  # pylint: disable=protected-access
            assert async_client
            assert async_client.ctx.max_until_disconnect == 7
            client.set_max_no_responses(9)
            assert async_client.ctx.max_until_disconnect == 9

        await asyncio.to_thread(run)

    async def test_decoder_shared(self, mock_server, client):
        """Test that the async client uses the decoder of the sync client."""
        assert mock_server

        def run():
            assert client.connect()
            async_client = client._async_client  # pylint: disable=protected-access
            assert async_client
            assert async_client.ctx.framer.decoder is client.framer.decoder

        await asyncio.to_thread(run)
