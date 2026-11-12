"""Test the sync tcp client, that runs the async client on a private loop."""

import asyncio
import socket
import threading

import pytest

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice


def free_port() -> int:
    """Return a free tcp port."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ServerThread:  # pylint: disable=too-few-public-methods
    """Tcp server on its own loop, so a sync client can block the test thread."""

    def __init__(self, port: int) -> None:
        """Start the server."""
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, name="test server")
        self.thread.start()
        device = SimDevice(
            0, SimData(0, datatype=DataType.REGISTERS, values=[17] * 100)
        )

        async def start() -> ModbusTcpServer:
            server = ModbusTcpServer(device, address=("127.0.0.1", port))
            await server.listen()
            return server

        self.server = asyncio.run_coroutine_threadsafe(start(), self.loop).result()

    def stop(self) -> None:
        """Stop the server."""
        asyncio.run_coroutine_threadsafe(self.server.shutdown(), self.loop).result()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
        self.loop.close()


@pytest.fixture(name="port")
def fixture_port():
    """Return a port with a running server."""
    port = free_port()
    server = ServerThread(port)
    yield port
    server.stop()


def client_threads() -> list[threading.Thread]:
    """Return the threads of the private loops."""
    return [t for t in threading.enumerate() if t.name == "pymodbus-sync-client"]


class TestSyncClientLoop:
    """Test the sync tcp client."""

    def test_read(self, port):
        """Test requests, and that close stops the private loop."""
        client = ModbusTcpClient("127.0.0.1", port=port)
        assert not client.connected
        assert client.connect()
        assert client.connected
        assert len(client_threads()) == 1
        for _ in range(3):
            rr = client.read_holding_registers(0, count=10)
            assert rr.registers == [17] * 10
        client.close()
        assert not client.connected
        assert not client_threads()

    def test_connect_on_request(self, port):
        """Test that a request connects, and connects again after close."""
        client = ModbusTcpClient("127.0.0.1", port=port)
        assert client.read_holding_registers(0, count=1).registers == [17]
        client.close()
        assert client.read_holding_registers(0, count=1).registers == [17]
        client.close()
        assert not client_threads()

    def test_with(self, port):
        """Test the with block."""
        with ModbusTcpClient("127.0.0.1", port=port) as client:
            assert client.read_holding_registers(0, count=1).registers == [17]
        assert not client.connected
        assert not client_threads()

    def test_connect_fails(self):
        """Test that a failed connect does not leave the private loop running."""
        client = ModbusTcpClient("127.0.0.1", port=free_port(), timeout=0.5)
        assert not client.connect()
        assert not client_threads()
        with pytest.raises(ConnectionException):
            client.read_holding_registers(0, count=1)
        assert not client_threads()
        client.close()

    async def test_in_running_loop(self, port):
        """Test the sync client, called from a thread that runs a loop."""
        client = ModbusTcpClient("127.0.0.1", port=port)
        assert client.read_holding_registers(0, count=1).registers == [17]
        client.close()

    def test_set_max_no_responses(self, port):
        """Test that the setting reaches the async client."""
        client = ModbusTcpClient("127.0.0.1", port=port)
        client.set_max_no_responses(7)
        assert client.connect()
        async_client = client._async_client  # pylint: disable=protected-access
        assert async_client
        assert async_client.ctx.max_until_disconnect == 7
        client.set_max_no_responses(9)
        assert async_client.ctx.max_until_disconnect == 9
        client.close()
