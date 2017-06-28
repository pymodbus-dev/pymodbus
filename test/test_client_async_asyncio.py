from unittest import mock
from pymodbus.client.async_asyncio import ReconnectingAsyncioModbusTcpClient, ModbusClientProtocol
from test.asyncio_test_helper import return_as_coroutine, run_coroutine


def test_protocol_connection_state_propagation_to_factory():
    protocol = ModbusClientProtocol()
    assert protocol.factory is None
    assert protocol.transport is None
    assert not protocol._connected

    protocol.factory = mock.MagicMock()

    protocol.connection_made(mock.sentinel.TRANSPORT)
    assert protocol.transport is mock.sentinel.TRANSPORT
    protocol.factory.protocol_made_connection.assert_called_once_with(protocol)
    assert protocol.factory.protocol_lost_connection.call_count == 0

    protocol.factory.reset_mock()

    protocol.connection_lost(mock.sentinel.REASON)
    assert protocol.transport is None
    assert protocol.factory.protocol_made_connection.call_count == 0
    protocol.factory.protocol_lost_connection.assert_called_once_with(protocol)


def test_factory_initialization_state():
    mock_protocol_class = mock.MagicMock()
    mock_loop = mock.MagicMock()
    client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)
    assert not client.connected
    assert client.delay_ms < client.DELAY_MAX_MS

    assert client.loop is mock_loop
    assert client.protocol_class is mock_protocol_class


def test_factory_reset_wait_before_reconnect():
    mock_protocol_class = mock.MagicMock()
    mock_loop = mock.MagicMock()
    client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)
    initial_delay = client.delay_ms
    assert initial_delay > 0
    client.delay_ms *= 2

    assert client.delay_ms > initial_delay
    client.reset_delay()
    assert client.delay_ms == initial_delay


def test_factory_stop():
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


def test_factory_protocol_made_connection():
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


@mock.patch('pymodbus.client.async_asyncio.asyncio.async')
def test_factory_protocol_lost_connection(mock_async):
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

    with mock.patch('pymodbus.client.async_asyncio.ReconnectingAsyncioModbusTcpClient._reconnect') as mock_reconnect:
        mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR
        client.protocol_lost_connection(mock.sentinel.PROTOCOL)
        mock_async.assert_called_once_with(mock.sentinel.RECONNECT_GENERATOR, loop=mock_loop)
    assert not client.connected
    assert client.protocol is None


@mock.patch('pymodbus.client.async_asyncio.asyncio.async')
def test_factory_start_success(mock_async):
    mock_protocol_class = mock.MagicMock()
    mock_loop = mock.MagicMock()
    client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

    run_coroutine(client.start(mock.sentinel.HOST, mock.sentinel.PORT))
    mock_loop.create_connection.assert_called_once_with(mock.ANY, mock.sentinel.HOST, mock.sentinel.PORT)
    assert mock_async.call_count == 0


@mock.patch('pymodbus.client.async_asyncio.asyncio.async')
def test_factory_start_failing_and_retried(mock_async):
    mock_protocol_class = mock.MagicMock()
    mock_loop = mock.MagicMock()
    mock_loop.create_connection = mock.MagicMock(side_effect=Exception('Did not work.'))
    client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

    # check whether reconnect is called upon failed connection attempt:
    with mock.patch('pymodbus.client.async_asyncio.ReconnectingAsyncioModbusTcpClient._reconnect') as mock_reconnect:
        mock_reconnect.return_value = mock.sentinel.RECONNECT_GENERATOR
        run_coroutine(client.start(mock.sentinel.HOST, mock.sentinel.PORT))
        mock_reconnect.assert_called_once_with()
        mock_async.assert_called_once_with(mock.sentinel.RECONNECT_GENERATOR, loop=mock_loop)


@mock.patch('pymodbus.client.async_asyncio.asyncio.sleep')
def test_factory_reconnect(mock_sleep):
    mock_protocol_class = mock.MagicMock()
    mock_loop = mock.MagicMock()
    client = ReconnectingAsyncioModbusTcpClient(protocol_class=mock_protocol_class, loop=mock_loop)

    client.delay_ms = 5000

    mock_sleep.side_effect = return_as_coroutine()
    run_coroutine(client._reconnect())
    mock_sleep.assert_called_once_with(5)
    assert mock_loop.create_connection.call_count == 1
