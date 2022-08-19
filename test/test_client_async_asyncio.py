"""Test client asyncio."""
import asyncio
from unittest import mock


from test.asyncio_test_helper import return_as_coroutine, run_coroutine

from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse
from pymodbus.client.base import ModbusClientProtocol
from pymodbus.client import (
    AsyncModbusUdpClient,
    AsyncModbusTlsClient,
    AsyncModbusTcpClient,
)
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer


def mock_asyncio_gather(coro):
    """Mock asyncio gather."""
    return coro


class TestAsyncioClient:
    """Test asyncio client."""

    def test_base_modbus_async_client_protocol(self):
        """Test base modbus async client protocol."""
        protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
        assert protocol.factory is None  # nosec
        assert protocol.transport is None  # nosec
        assert not protocol._connected  # nosec pylint: disable=protected-access

    def test_protocol_connection_state_propagation_to_factory(
        self,
    ):
        """Test protocol connection state progration to factory."""
        protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
        assert protocol.factory is None  # nosec
        assert protocol.transport is None  # nosec
        assert not protocol._connected  # nosec pylint: disable=protected-access

        protocol.factory = mock.MagicMock()

        protocol.connection_made(mock.sentinel.TRANSPORT)
        assert protocol.transport is mock.sentinel.TRANSPORT  # nosec
        protocol.factory.protocol_made_connection.assert_called_once_with(  # pylint: disable=no-member
            protocol
        )
        assert (
            not protocol.factory.protocol_lost_connection.call_count  # nosec pylint: disable=no-member
        )

        protocol.factory.reset_mock()

        protocol.connection_lost(mock.sentinel.REASON)
        assert protocol.transport is None  # nosec
        assert (
            not protocol.factory.protocol_made_connection.call_count  # nosec pylint: disable=no-member
        )
        protocol.factory.protocol_lost_connection.assert_called_once_with(  # pylint: disable=no-member
            protocol
        )
        protocol.raise_future = mock.MagicMock()
        request = mock.MagicMock()
        protocol.transaction.addTransaction(request, 1)
        protocol.connection_lost(mock.sentinel.REASON)
        call_args = protocol.raise_future.call_args.args
        protocol.raise_future.assert_called_once()
        assert call_args[0] == request  # nosec
        assert isinstance(call_args[1], ConnectionException)  # nosec

    async def test_factory_initialization_state(self):
        """Test factory initialization state."""
        mock_protocol_class = mock.MagicMock()
        client = AsyncModbusTcpClient(
            "127.0.0.1",
            protocol_class=mock_protocol_class
        )
        assert not client.connected  # nosec

    async def test_initialization_tcp_in_loop(self):
        """Test initialization tcp in loop."""
        client = AsyncModbusTcpClient("127.0.0.1", port=5020)
        assert not client.connected  # nosec
        assert client.params.port == 5020  # nosec

    async def test_initialization_udp_in_loop(self):
        """Test initialization udp in loop."""
        client = AsyncModbusUdpClient("127.0.0.1")
        await client.connect()
        # TBD assert client.connected  # nosec
        assert client.params.port == 502  # nosec

    async def test_initialization_tls_in_loop(self):
        """Test initialization tls in loop."""
        client = AsyncModbusTlsClient("127.0.0.1")
        assert not client.connected  # nosec
        assert client.params.port == 802  # nosec

    async def test_factory_reset_wait_before_reconnect(self):
        """Test factory reset wait before reconnect."""
        mock_protocol_class = mock.MagicMock()
        client = AsyncModbusTcpClient(
            "127.0.0.1",
            protocol_class=mock_protocol_class
        )
        initial_delay = client.delay_ms
        assert initial_delay > 0  # nosec
        client.delay_ms *= 2

        assert client.delay_ms > initial_delay  # nosec
        client.reset_delay()
        assert client.delay_ms == initial_delay  # nosec

    async def test_factory_stop(self):
        """Test factory stop."""
        mock_protocol_class = mock.MagicMock()
        client = AsyncModbusTcpClient(
            "127.0.0.1",
            protocol_class=mock_protocol_class
        )
        assert not client.connected  # nosec
        await client.close()
        assert not client.connected  # nosec

        # fake connected client:
        client.protocol = mock.MagicMock()
        client.connected = True

        await client.close()
        client.protocol.transport.close.assert_called_once_with()

    async def test_factory_protocol_made_connection(self):
        """Test factory protocol made connection."""
        mock_protocol_class = mock.MagicMock()
        client = AsyncModbusTcpClient(
            "127.0.0.1",
            protocol_class=mock_protocol_class
        )
        assert not client.connected  # nosec
        assert client.protocol is None  # nosec
        client.protocol_made_connection(mock.sentinel.PROTOCOL)
        assert client.connected  # nosec
        assert client.protocol is mock.sentinel.PROTOCOL  # nosec

        client.protocol_made_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
        assert client.connected  # nosec
        assert client.protocol is mock.sentinel.PROTOCOL  # nosec

    async def test_factory_protocol_lost_connection(self):
        """Test factory protocol lost connection."""
        mock_protocol_class = mock.MagicMock()
        client = AsyncModbusTcpClient(
            "127.0.0.1",
            protocol_class=mock_protocol_class
        )
        assert not client.connected  # nosec
        assert client.protocol is None  # nosec

        # fake client is connected and *then* looses connection:
        client.connected = True
        client.params.host = mock.sentinel.HOST
        client.params.port = mock.sentinel.PORT
        client.protocol = mock.sentinel.PROTOCOL
        client.protocol_lost_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
        assert not client.connected  # nosec

        client.connected = True
        with mock.patch(
            "pymodbus.client.async_tcp."
            "AsyncModbusTcpClient._reconnect"
        ) as mock_reconnect:
            mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR

            client.protocol_lost_connection(mock.sentinel.PROTOCOL)
        assert not client.connected  # nosec
        assert client.protocol is None  # nosec

    async def test_factory_start_success(self):
        """Test factory start success."""
        mock_protocol_class = mock.MagicMock()
        client = AsyncModbusTcpClient(
            mock.sentinel.HOST,
            port=mock.sentinel.PORT,
            protocol_class=mock_protocol_class
        )
        await client.connect()

    @mock.patch("pymodbus.client.async_tcp.asyncio.ensure_future")
    async def test_factory_start_failing_and_retried(self, mock_async):  # pylint: disable=unused-argument
        """Test factory start failing and retried."""
        mock_protocol_class = mock.MagicMock()
        loop = asyncio.get_running_loop()
        loop.create_connection = mock.MagicMock(
            side_effect=Exception("Did not work.")
        )
        client = AsyncModbusTcpClient(
            mock.sentinel.HOST,
            port=mock.sentinel.PORT,
            protocol_class=mock_protocol_class
        )

        # check whether reconnect is called upon failed connection attempt:
        with mock.patch(
            "pymodbus.client.async_tcp"
            ".AsyncModbusTcpClient._reconnect"
        ) as mock_reconnect:
            mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR
            run_coroutine(client.connect())
            mock_reconnect.assert_called_once_with()

    @mock.patch("pymodbus.client.async_tcp.asyncio.sleep")
    async def test_factory_reconnect(self, mock_sleep):
        """Test factory reconnect."""
        mock_protocol_class = mock.MagicMock()
        mock_sleep.side_effect = return_as_coroutine()
        loop = asyncio.get_running_loop()
        loop.create_connection = mock.MagicMock(return_value=(None, None))
        client = AsyncModbusTcpClient(
            "127.0.0.1",
            protocol_class=mock_protocol_class
        )
        client.delay_ms = 5000
        await client.connect()

        run_coroutine(client._reconnect())  # pylint: disable=protected-access
        mock_sleep.assert_called_once_with(5)
        assert loop.create_connection.call_count >= 1  # nosec

    def test_client_protocol_connection_made(self):
        """Test the client protocol close."""
        protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
        transport = mock.MagicMock()
        factory = mock.MagicMock()
        if isinstance(protocol, ModbusClientProtocol):
            protocol.factory = factory
        protocol.connection_made(transport)
        assert protocol.transport == transport  # nosec
        assert protocol.connected  # nosec
        if isinstance(protocol, ModbusClientProtocol):
            assert (
                protocol.factory.protocol_made_connection.call_count == 1  # pylint: disable=no-member
            )  # nosec

    async def test_client_protocol_close(
        self,
    ):
        """Test the client protocol close."""
        protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
        transport = mock.MagicMock()
        factory = mock.MagicMock()
        if isinstance(protocol, ModbusClientProtocol):
            protocol.factory = factory
        protocol.connection_made(transport)
        assert protocol.transport == transport  # nosec
        assert protocol.connected  # nosec
        await protocol.close()
        transport.close.assert_called_once_with()
        assert not protocol.connected  # nosec

    def test_client_protocol_connection_lost(self):
        """Test the client protocol connection lost"""
        protocol = ModbusClientProtocol("127.0.0.1", framer=ModbusSocketFramer, timeout=0)
        protocol.execute = mock.MagicMock()
        transport = mock.MagicMock()
        factory = mock.MagicMock()
        if isinstance(protocol, ModbusClientProtocol):
            protocol.factory = factory
        protocol.connection_made(transport)
        protocol.transport.write = mock.Mock()

        request = ReadCoilsRequest(1, 1)
        response = protocol.execute(request)
        protocol.connection_lost("REASON")
        excp = response.exception()  # noqa: F841
        # assert isinstance(excp, ConnectionException)  # nosec
        if isinstance(protocol, ModbusClientProtocol):
            assert (
                protocol.factory.protocol_lost_connection.call_count == 1  # pylint: disable=no-member
            )  # nosec

    async def test_client_protocol_data_received(self):
        """Test the client protocol data received"""
        protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
        transport = mock.MagicMock()
        protocol.connection_made(transport)
        assert protocol.transport == transport  # nosec
        assert protocol.connected  # nosec
        data = b"\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04"

        # setup existing request
        response = protocol._build_response(  # pylint: disable=protected-access
            0x00
        )
        protocol.data_received(data)
        result = response.result()
        assert isinstance(result, ReadCoilsResponse)  # nosec

    async def test_client_protocol_execute(self):
        """Test the client protocol execute method"""
        protocol = ModbusClientProtocol("127.0.0.1", framer=ModbusSocketFramer)
        protocol.create_future = mock.MagicMock()
        fut = asyncio.Future()
        fut.set_result(fut)
        protocol.create_future.return_value = fut
        transport = mock.MagicMock()
        protocol.connection_made(transport)
        protocol.transport.write = mock.Mock()

        request = ReadCoilsRequest(1, 1)
        response = await protocol.execute(request)
        tid = request.transaction_id
        f_trans = protocol.transaction.getTransaction(tid)
        assert response == f_trans  # nosec

    async def test_client_protocol_handle_response(self):
        """Test the client protocol handles responses"""
        protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
        transport = mock.MagicMock()
        protocol.connection_made(transport=transport)
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00
        # if isinstance(protocol.create_future, mock.MagicMock):
        #     import asyncio
        #     protocol.create_future.return_value = asyncio.Future()
        # handle skipped cases
        protocol._handle_response(None)  # pylint: disable=protected-access
        protocol._handle_response(reply)  # pylint: disable=protected-access

        # handle existing cases
        response = protocol._build_response(  # pylint: disable=protected-access
            0x00
        )
        protocol._handle_response(reply)  # pylint: disable=protected-access
        result = response.result()
        assert result == reply  # nosec

    async def test_client_protocol_build_response(self):
        """Test the udp client protocol builds responses"""
        protocol = ModbusClientProtocol(framer=ModbusSocketFramer)
        assert not len(  # nosec pylint: disable=use-implicit-booleaness-not-len
            list(protocol.transaction)
        )
        response = protocol._build_response(  # pylint: disable=protected-access
            0x00
        )
        excp = response.exception()
        assert isinstance(excp, ConnectionException)  # nosec
        assert not len(  # nosec pylint: disable=use-implicit-booleaness-not-len
            list(protocol.transaction)
        )

        protocol._connected = True  # pylint: disable=protected-access
        protocol._build_response(0x00)  # pylint: disable=protected-access
        assert len(list(protocol.transaction)) == 1  # nosec
