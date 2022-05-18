"""Test client asyncio."""
import sys
from unittest import mock
from test.asyncio_test_helper import return_as_coroutine, run_coroutine
import asyncio
import pytest
from pymodbus.client.asynchronous.async_io import (
    BaseModbusAsyncClientProtocol,
    ReconnectingAsyncioModbusTcpClient,
    ModbusClientProtocol,
    ModbusUdpClientProtocol,
)
from pymodbus.client.asynchronous import schedulers
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient
from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient

protocols = [
    BaseModbusAsyncClientProtocol,
    ModbusUdpClientProtocol,
    ModbusClientProtocol,
]


class TestAsyncioClient:
    """Test asyncio client."""

    def test_base_modbus_async_client_protocol(self):  # pylint: disable=no-self-use
        """Test base modbus async client protocol."""
        protocol = BaseModbusAsyncClientProtocol()
        assert protocol.factory is None  # nosec
        assert protocol.transport is None  # nosec
        assert not protocol._connected  # nosec pylint: disable=protected-access

    def test_protocol_connection_state_propagation_to_factory(
        self,
    ):  # pylint: disable=no-self-use
        """Test protocol connection state progration to factory."""
        protocol = ModbusClientProtocol()
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
        if sys.version_info.major == 3 and sys.version_info.minor >= 8:
            call_args = protocol.raise_future.call_args.args
        else:
            call_args = protocol.raise_future.call_args[0]
        protocol.raise_future.assert_called_once()
        assert call_args[0] == request  # nosec
        assert isinstance(call_args[1], ConnectionException)  # nosec

    def test_factory_initialization_state(self):  # pylint: disable=no-self-use
        """Test factory initialization state."""
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(
            protocol_class=mock_protocol_class, loop=mock_loop
        )
        assert not client.connected  # nosec
        assert client.delay_ms < client.DELAY_MAX_MS  # nosec

        assert client.loop is mock_loop  # nosec
        assert client.protocol_class is mock_protocol_class  # nosec

    @pytest.mark.asyncio
    async def test_initialization_tcp_in_loop(self):  # pylint: disable=no-self-use
        """Test initialization tcp in loop."""
        _, client = AsyncModbusTCPClient(  # NOSONAR pylint: disable=unpacking-non-sequence
            schedulers.ASYNC_IO,
            port=5020,
        )
        client = await client

        assert not client.connected  # nosec
        assert client.port == 5020  # nosec
        assert client.delay_ms < client.DELAY_MAX_MS  # nosec

    @pytest.mark.asyncio
    async def test_initialization_udp_in_loop(self):  # pylint: disable=no-self-use
        """Test initialization udp in loop."""
        _, client = AsyncModbusUDPClient(  # NOSONAR # pylint: disable=unpacking-non-sequence
            schedulers.ASYNC_IO, port=5020
        )
        client = await client

        assert client.connected  # nosec
        assert client.port == 5020  # nosec
        assert client.delay_ms < client.DELAY_MAX_MS  # nosec

    @pytest.mark.asyncio
    async def test_initialization_tls_in_loop(self):  # pylint: disable=no-self-use
        """Test initialization tls in loop."""
        _, client = AsyncModbusTLSClient(  # NOSONAR pylint: disable=unpacking-non-sequence
            schedulers.ASYNC_IO, port=5020
        )
        client = await client

        assert not client.connected  # nosec
        assert client.port == 5020  # nosec
        assert client.delay_ms < client.DELAY_MAX_MS  # nosec

    @pytest.mark.asyncio
    def test_initialization_serial_in_loop(self):  # pylint: disable=no-self-use
        """Test initialization serial in loop."""
        _, client = AsyncModbusSerialClient(  # NOSONAR pylint: disable=unpacking-non-sequence
            schedulers.ASYNC_IO, port="/tmp/ptyp0", baudrate=9600, method="rtu"  # NOSONAR #nosec
        )
        assert client.port == "/tmp/ptyp0"  # nosec NOSONAR
        assert client.baudrate == 9600  # nosec

    def test_factory_reset_wait_before_reconnect(self):  # pylint: disable=no-self-use
        """Test factory reset wait before reconnect."""
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(
            protocol_class=mock_protocol_class, loop=mock_loop
        )
        initial_delay = client.delay_ms
        assert initial_delay > 0  # nosec
        client.delay_ms *= 2

        assert client.delay_ms > initial_delay  # nosec
        client.reset_delay()
        assert client.delay_ms == initial_delay  # nosec

    def test_factory_stop(self):  # pylint: disable=no-self-use
        """Test factory stop."""
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(
            protocol_class=mock_protocol_class, loop=mock_loop
        )
        assert not client.connected  # nosec
        client.stop()
        assert not client.connected  # nosec

        # fake connected client:
        client.protocol = mock.MagicMock()
        client.connected = True

        client.stop()
        client.protocol.transport.close.assert_called_once_with()

    def test_factory_protocol_made_connection(self):  # pylint: disable=no-self-use
        """Test factory protocol made connection."""
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(
            protocol_class=mock_protocol_class, loop=mock_loop
        )
        assert not client.connected  # nosec
        assert client.protocol is None  # nosec
        client.protocol_made_connection(mock.sentinel.PROTOCOL)
        assert client.connected  # nosec
        assert client.protocol is mock.sentinel.PROTOCOL  # nosec

        client.protocol_made_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
        assert client.connected  # nosec
        assert client.protocol is mock.sentinel.PROTOCOL  # nosec

    @mock.patch("pymodbus.client.asynchronous.async_io.asyncio.ensure_future")
    def test_factory_protocol_lost_connection(
        self, mock_async
    ):  # pylint: disable=no-self-use
        """Test factory protocol lost connection."""
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(
            protocol_class=mock_protocol_class, loop=mock_loop
        )
        assert not client.connected  # nosec
        assert client.protocol is None  # nosec

        # fake client is connected and *then* looses connection:
        client.connected = True
        client.host = mock.sentinel.HOST
        client.port = mock.sentinel.PORT
        client.protocol = mock.sentinel.PROTOCOL
        client.protocol_lost_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
        mock_async.reset_mock()
        assert not client.connected  # nosec

        client.connected = True
        with mock.patch(
            "pymodbus.client.asynchronous.async_io."
            "ReconnectingAsyncioModbusTcpClient._reconnect"
        ) as mock_reconnect:
            mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR

            client.protocol_lost_connection(mock.sentinel.PROTOCOL)
            if sys.version_info == (3, 7):
                mock_async.assert_called_once_with(
                    mock.sentinel.RECONNECT_GENERATOR, loop=mock_loop
                )
        assert not client.connected  # nosec
        assert client.protocol is None  # nosec

    @pytest.mark.asyncio
    async def test_factory_start_success(self):  # pylint: disable=no-self-use
        """Test factory start success."""
        mock_protocol_class = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class)
        await client.start(mock.sentinel.HOST, mock.sentinel.PORT)

    @mock.patch("pymodbus.client.asynchronous.async_io.asyncio.ensure_future")
    def test_factory_start_failing_and_retried(
        self, mock_async
    ):  # pylint: disable=no-self-use
        """Test factory start failing and retried."""
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        mock_loop.create_connection = mock.MagicMock(
            side_effect=Exception("Did not work.")
        )
        client = ReconnectingAsyncioModbusTcpClient(
            protocol_class=mock_protocol_class, loop=mock_loop
        )

        # check whether reconnect is called upon failed connection attempt:
        with mock.patch(
            "pymodbus.client.asynchronous.async_io"
            ".ReconnectingAsyncioModbusTcpClient._reconnect"
        ) as mock_reconnect:
            mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR
            run_coroutine(client.start(mock.sentinel.HOST, mock.sentinel.PORT))
            mock_reconnect.assert_called_once_with()
            if sys.version_info == (3, 7):
                mock_async.assert_called_once_with(
                    mock.sentinel.RECONNECT_GENERATOR, loop=mock_loop
                )

    # @pytest.mark.asyncio
    @mock.patch("pymodbus.client.asynchronous.async_io.asyncio.sleep")
    def test_factory_reconnect(self, mock_sleep):  # pylint: disable=no-self-use
        """Test factory reconnect."""
        mock_protocol_class = mock.MagicMock()
        mock_sleep.side_effect = return_as_coroutine()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(
            protocol_class=mock_protocol_class, loop=mock_loop
        )
        client.delay_ms = 5000

        run_coroutine(client._reconnect())  # pylint: disable=protected-access
        mock_sleep.assert_called_once_with(5)
        assert mock_loop.create_connection.call_count == 1  # nosec

    @pytest.mark.parametrize("protocol", protocols)
    def test_client_protocol_connection_made(
        self, protocol
    ):  # pylint: disable=no-self-use
        """Test the client protocol close."""
        protocol = protocol(ModbusSocketFramer(ClientDecoder()))
        transport = mock.MagicMock()
        factory = mock.MagicMock()
        if isinstance(protocol, ModbusUdpClientProtocol):
            protocol.factory = factory
        protocol.connection_made(transport)
        assert protocol.transport == transport  # nosec
        assert protocol.connected  # nosec
        if isinstance(protocol, ModbusUdpClientProtocol):
            assert protocol.factory.protocol_made_connection.call_count == 1  # nosec

    @pytest.mark.parametrize("protocol", protocols)
    def test_client_protocol_close(self, protocol):  # pylint: disable=no-self-use
        """Test the client protocol close."""
        protocol = protocol(ModbusSocketFramer(ClientDecoder()))
        transport = mock.MagicMock()
        factory = mock.MagicMock()
        if isinstance(protocol, ModbusUdpClientProtocol):
            protocol.factory = factory
        protocol.connection_made(transport)
        assert protocol.transport == transport  # nosec
        assert protocol.connected  # nosec
        protocol.close()
        transport.close.assert_called_once_with()
        assert not protocol.connected  # nosec

    @pytest.mark.skip("To fix")
    @pytest.mark.parametrize("protocol", protocols)
    def test_client_protocol_connection_lost(
        self, protocol
    ):  # pylint: disable=no-self-use
        """Test the client protocol connection lost"""
        framer = ModbusSocketFramer(None)
        protocol = protocol(framer=framer, timeout=0)
        protocol.execute = mock.MagicMock()
        # future = asyncio.Future()
        # future.set_result(ReadCoilsResponse([1]))
        # protocol._execute = mock.MagicMock(side_effect=future)
        transport = mock.MagicMock()
        factory = mock.MagicMock()
        if isinstance(protocol, ModbusUdpClientProtocol):
            protocol.factory = factory
        protocol.connection_made(transport)
        protocol.transport.write = mock.Mock()

        request = ReadCoilsRequest(1, 1)
        response = protocol.execute(request)
        # d = await d
        protocol.connection_lost("REASON")
        excp = response.exception()
        assert isinstance(excp, ConnectionException)  # nosec
        if isinstance(protocol, ModbusUdpClientProtocol):
            assert protocol.factory.protocol_lost_connection.call_count == 1  # nosec

    @pytest.mark.parametrize("protocol", protocols)
    async def test_client_protocol_data_received(
        self, protocol
    ):  # pylint: disable=no-self-use
        """Test the client protocol data received"""
        protocol = protocol(ModbusSocketFramer(ClientDecoder()))
        transport = mock.MagicMock()
        protocol.connection_made(transport)
        assert protocol.transport == transport  # nosec
        assert protocol.connected  # nosec
        data = b"\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04"

        # setup existing request
        response = protocol._buildResponse(0x00)  # pylint: disable=protected-access
        if isinstance(protocol, ModbusUdpClientProtocol):
            protocol.datagram_received(data, None)
        else:
            protocol.data_received(data)
        result = response.result()
        assert isinstance(result, ReadCoilsResponse)  # nosec

    # @pytest.mark.skip("To fix")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("protocol", protocols)
    async def test_client_protocol_execute(
        self, protocol
    ):  # pylint: disable=no-self-use
        """Test the client protocol execute method"""
        framer = ModbusSocketFramer(None)
        protocol = protocol(framer=framer)
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

    @pytest.mark.parametrize("protocol", protocols)
    async def test_client_protocol_handle_response(
        self, protocol
    ):  # pylint: disable=no-self-use
        """Test the client protocol handles responses"""
        protocol = protocol()
        transport = mock.MagicMock()
        protocol.connection_made(transport=transport)
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00
        # if isinstance(protocol.create_future, mock.MagicMock):
        #     import asyncio
        #     protocol.create_future.return_value = asyncio.Future()
        # handle skipped cases
        protocol._handleResponse(None)  # pylint: disable=protected-access
        protocol._handleResponse(reply)  # pylint: disable=protected-access

        # handle existing cases
        response = protocol._buildResponse(0x00)  # pylint: disable=protected-access
        protocol._handleResponse(reply)  # pylint: disable=protected-access
        result = response.result()
        assert result == reply  # nosec

    @pytest.mark.parametrize("protocol", protocols)
    async def test_client_protocol_build_response(
        self, protocol
    ):  # pylint: disable=no-self-use
        """Test the udp client protocol builds responses"""
        protocol = protocol()
        assert not len(  # nosec pylint: disable=use-implicit-booleaness-not-len
            list(protocol.transaction)
        )
        response = protocol._buildResponse(  # nosec pylint: disable=protected-access
            0x00
        )
        excp = response.exception()
        assert isinstance(excp, ConnectionException)  # nosec
        assert not len(  # nosec pylint: disable=use-implicit-booleaness-not-len
            list(protocol.transaction)
        )

        protocol._connected = True  # pylint: disable=protected-access
        protocol._buildResponse(0x00)  # pylint: disable=protected-access
        assert len(list(protocol.transaction)) == 1  # nosec
