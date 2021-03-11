from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
import pytest
if IS_PYTHON3 and PYTHON_VERSION >= (3, 4):
    import asyncio
    from unittest import mock
    from pymodbus.client.asynchronous.async_io import (
        BaseModbusAsyncClientProtocol,
        ReconnectingAsyncioModbusTcpClient,
        ModbusClientProtocol, ModbusUdpClientProtocol)
    from test.asyncio_test_helper import return_as_coroutine, run_coroutine
    from pymodbus.client.asynchronous import schedulers
    from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
    from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
    from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
    from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient
    from pymodbus.factory import ClientDecoder
    from pymodbus.exceptions import ConnectionException
    from pymodbus.transaction import ModbusSocketFramer
    from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse
    protocols = [BaseModbusAsyncClientProtocol, ModbusUdpClientProtocol, ModbusClientProtocol]
else:
    import mock
    protocols = [None, None]


@pytest.mark.skipif(not IS_PYTHON3, reason="requires python3.4 or above")
class TestAsyncioClient(object):
    def test_base_modbus_async_client_protocol(self):
        protocol = BaseModbusAsyncClientProtocol()
        assert protocol.factory is None
        assert protocol.transport is None
        assert not protocol._connected

    def test_protocol_connection_state_propagation_to_factory(self):
        protocol = ModbusClientProtocol()
        assert protocol.factory is None
        assert protocol.transport is None
        assert not protocol._connected

        protocol.factory = mock.MagicMock()

        protocol.connection_made(mock.sentinel.TRANSPORT)
        assert protocol.transport is mock.sentinel.TRANSPORT
        protocol.factory.protocol_made_connection.assert_called_once_with(
            protocol)
        assert protocol.factory.protocol_lost_connection.call_count == 0

        protocol.factory.reset_mock()

        protocol.connection_lost(mock.sentinel.REASON)
        assert protocol.transport is None
        assert protocol.factory.protocol_made_connection.call_count == 0
        protocol.factory.protocol_lost_connection.assert_called_once_with(
            protocol)
        protocol.raise_future = mock.MagicMock()
        request = mock.MagicMock()
        protocol.transaction.addTransaction(request, 1)
        protocol.connection_lost(mock.sentinel.REASON)
        if PYTHON_VERSION.major == 3 and PYTHON_VERSION.minor >= 8:
            call_args = protocol.raise_future.call_args.args
        else:
            call_args = protocol.raise_future.call_args[0]
        protocol.raise_future.assert_called_once()
        assert call_args[0] == request
        assert isinstance(call_args[1], ConnectionException)

    def test_factory_initialization_state(self):
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)
        assert not client.connected
        assert client.delay_ms < client.DELAY_MAX_MS

        assert client.loop is mock_loop
        assert client.protocol_class is mock_protocol_class

    @pytest.mark.asyncio
    async def test_initialization_tcp_in_loop(self):
        _, client = AsyncModbusTCPClient(schedulers.ASYNC_IO,
                                         port=5020)
        client = await client

        assert not client.connected
        assert client.port == 5020
        assert client.delay_ms < client.DELAY_MAX_MS

    @pytest.mark.asyncio
    async def test_initialization_udp_in_loop(self):
        _, client = AsyncModbusUDPClient(schedulers.ASYNC_IO, port=5020)
        client = await client

        assert client.connected
        assert client.port == 5020
        assert client.delay_ms < client.DELAY_MAX_MS

    @pytest.mark.asyncio
    async def test_initialization_tls_in_loop(self):
        _, client = AsyncModbusTLSClient(schedulers.ASYNC_IO, port=5020)
        client = await client

        assert not client.connected
        assert client.port == 5020
        assert client.delay_ms < client.DELAY_MAX_MS

    @pytest.mark.asyncio
    async def test_initialization_serial_in_loop(self):
        _, client = AsyncModbusSerialClient(schedulers.ASYNC_IO, port='/tmp/ptyp0', baudrate=9600, method='rtu')

        assert client.port == '/tmp/ptyp0'
        assert client.baudrate == 9600

    def test_factory_reset_wait_before_reconnect(self):
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)
        initial_delay = client.delay_ms
        assert initial_delay > 0
        client.delay_ms *= 2

        assert client.delay_ms > initial_delay
        client.reset_delay()
        assert client.delay_ms == initial_delay

    def test_factory_stop(self):
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

        assert not client.connected
        client.stop()
        assert not client.connected

        # fake connected client:
        client.protocol = mock.MagicMock()
        client.connected = True

        client.stop()
        client.protocol.transport.close.assert_called_once_with()

    def test_factory_protocol_made_connection(self):
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

        assert not client.connected
        assert client.protocol is None
        client.protocol_made_connection(mock.sentinel.PROTOCOL)
        assert client.connected
        assert client.protocol is mock.sentinel.PROTOCOL

        client.protocol_made_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
        assert client.connected
        assert client.protocol is mock.sentinel.PROTOCOL

    @mock.patch('pymodbus.client.asynchronous.async_io.asyncio.ensure_future')
    def test_factory_protocol_lost_connection(self, mock_async):
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

        assert not client.connected
        assert client.protocol is None
        client.protocol_lost_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
        assert not client.connected

        # fake client ist connected and *then* looses connection:
        client.connected = True
        client.host = mock.sentinel.HOST
        client.port = mock.sentinel.PORT
        client.protocol = mock.sentinel.PROTOCOL
        with mock.patch('pymodbus.client.asynchronous.async_io.ReconnectingAsyncioModbusTcpClient._reconnect') as mock_reconnect:
            mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR
            client.protocol_lost_connection(mock.sentinel.PROTOCOL)
            if PYTHON_VERSION <= (3, 7):
                mock_async.assert_called_once_with(mock.sentinel.RECONNECT_GENERATOR, loop=mock_loop)
        assert not client.connected
        assert client.protocol is None

    # @mock.patch('pymodbus.client.asynchronous.async_io.asyncio.ensure_future')
    @pytest.mark.asyncio
    async def test_factory_start_success(self):
        mock_protocol_class = mock.MagicMock()
        # mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class)
        # client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

        await client.start(mock.sentinel.HOST, mock.sentinel.PORT)
        # run_coroutine(client.start(mock.sentinel.HOST, mock.sentinel.PORT))
        # mock_loop.create_connection.assert_called_once_with(mock.ANY, mock.sentinel.HOST, mock.sentinel.PORT)
        # assert mock_async.call_count == 0

    @mock.patch('pymodbus.client.asynchronous.async_io.asyncio.ensure_future')
    def test_factory_start_failing_and_retried(self, mock_async):
        mock_protocol_class = mock.MagicMock()
        mock_loop = mock.MagicMock()
        mock_loop.create_connection = mock.MagicMock(side_effect=Exception('Did not work.'))
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

        # check whether reconnect is called upon failed connection attempt:
        with mock.patch('pymodbus.client.asynchronous.async_io.ReconnectingAsyncioModbusTcpClient._reconnect') as mock_reconnect:
            mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR
            run_coroutine(client.start(mock.sentinel.HOST, mock.sentinel.PORT))
            mock_reconnect.assert_called_once_with()
            if PYTHON_VERSION <= (3, 7):
                mock_async.assert_called_once_with(mock.sentinel.RECONNECT_GENERATOR, loop=mock_loop)

    # @pytest.mark.asyncio
    @mock.patch('pymodbus.client.asynchronous.async_io.asyncio.sleep')
    def test_factory_reconnect(self, mock_sleep):
        mock_protocol_class = mock.MagicMock()
        mock_sleep.side_effect = return_as_coroutine()
        mock_loop = mock.MagicMock()
        client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

        client.delay_ms = 5000

        run_coroutine(client._reconnect())
        mock_sleep.assert_called_once_with(5)
        assert mock_loop.create_connection.call_count == 1

    @pytest.mark.parametrize("protocol", protocols)
    def testClientProtocolConnectionMade(self, protocol):
        """
        Test the client protocol close
        :return:
        """
        protocol = protocol(ModbusSocketFramer(ClientDecoder()))
        transport = mock.MagicMock()
        factory = mock.MagicMock()
        if isinstance(protocol, ModbusUdpClientProtocol):
            protocol.factory = factory
        protocol.connection_made(transport)
        assert protocol.transport == transport
        assert protocol.connected
        if isinstance(protocol, ModbusUdpClientProtocol):
            assert protocol.factory.protocol_made_connection.call_count == 1

    @pytest.mark.parametrize("protocol", protocols)
    def testClientProtocolClose(self, protocol):
        """
        Test the client protocol close
        :return:
        """
        protocol = protocol(ModbusSocketFramer(ClientDecoder()))
        transport = mock.MagicMock()
        factory = mock.MagicMock()
        if isinstance(protocol, ModbusUdpClientProtocol):
            protocol.factory = factory
        protocol.connection_made(transport)
        assert protocol.transport == transport
        assert protocol.connected
        protocol.close()
        transport.close.assert_called_once_with()
        assert not protocol.connected

    @pytest.mark.skip("To fix")
    @pytest.mark.parametrize("protocol", protocols)
    def testClientProtocolConnectionLost(self, protocol):
        ''' Test the client protocol connection lost'''
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
        d = protocol.execute(request)
        # d = await d
        protocol.connection_lost("REASON")
        excp = d.exception()
        assert (isinstance(excp, ConnectionException))
        if isinstance(protocol, ModbusUdpClientProtocol):
            assert protocol.factory.protocol_lost_connection.call_count == 1

    @pytest.mark.parametrize("protocol", protocols)
    def testClientProtocolDataReceived(self, protocol):
        ''' Test the client protocol data received '''
        protocol = protocol(ModbusSocketFramer(ClientDecoder()))
        transport = mock.MagicMock()
        protocol.connection_made(transport)
        assert protocol.transport == transport
        assert protocol.connected
        data = b'\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04'

        # setup existing request
        d = protocol._buildResponse(0x00)
        if isinstance(protocol, ModbusUdpClientProtocol):
            protocol.datagram_received(data, None)
        else:
            protocol.data_received(data)
        result = d.result()
        assert isinstance(result, ReadCoilsResponse)

    # @pytest.mark.skip("To fix")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("protocol", protocols)
    async def testClientProtocolExecute(self, protocol):
        ''' Test the client protocol execute method '''
        import asyncio
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
        d = await protocol.execute(request)
        tid = request.transaction_id
        f = protocol.transaction.getTransaction(tid)
        assert d == f

    @pytest.mark.parametrize("protocol", protocols)
    def testClientProtocolHandleResponse(self, protocol):
        ''' Test the client protocol handles responses '''
        protocol = protocol()
        transport = mock.MagicMock()
        protocol.connection_made(transport=transport)
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00
        # if isinstance(protocol.create_future, mock.MagicMock):
        #     import asyncio
        #     protocol.create_future.return_value = asyncio.Future()
        # handle skipped cases
        protocol._handleResponse(None)
        protocol._handleResponse(reply)

        # handle existing cases
        d = protocol._buildResponse(0x00)
        protocol._handleResponse(reply)
        result = d.result()
        assert result == reply

    @pytest.mark.parametrize("protocol", protocols)
    def testClientProtocolBuildResponse(self, protocol):
        ''' Test the udp client protocol builds responses '''
        protocol = protocol()
        # if isinstance(protocol.create_future, mock.MagicMock):
        #     import asyncio
        #     protocol.create_future.return_value = asyncio.Future()
        assert not len(list(protocol.transaction))

        d = protocol._buildResponse(0x00)
        excp = d.exception()
        assert (isinstance(excp, ConnectionException))
        assert not len(list(protocol.transaction))

        protocol._connected = True
        protocol._buildResponse(0x00)
        assert len(list(protocol.transaction)) == 1
