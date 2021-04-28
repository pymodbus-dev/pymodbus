from unittest import mock

import pytest
import trio
import outcome

from pymodbus.client.asynchronous.trio import (
    _EventAndValue,
    BaseModbusAsyncClientProtocol,
    ModbusTcpClientProtocol,
    TrioModbusTcpClient,
    init_tcp_client,
)
from pymodbus.exceptions import ConnectionException
from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
)


protocols = [ModbusTcpClientProtocol]


def test_factory_stop():
    mock_protocol_class = mock.Mock()
    client = TrioModbusTcpClient(protocol_class=mock_protocol_class)

    assert not client.connected
    client.stop()
    assert not client.connected

    # fake connected client:
    client.protocol = mock.Mock()
    client.connected = True

    client.stop()
    client.protocol.transport.close.assert_called_once_with()

def test_factory_protocol_made_connection():
    mock_protocol_class = mock.Mock()
    client = TrioModbusTcpClient(protocol_class=mock_protocol_class)

    assert not client.connected
    assert client.protocol is None
    client.protocol_made_connection(mock.sentinel.PROTOCOL)
    assert client.connected
    assert client.protocol is mock.sentinel.PROTOCOL

    client.protocol_made_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
    assert client.connected
    assert client.protocol is mock.sentinel.PROTOCOL


async def aag(*args, **kwargs):
    return trio.testing.MemoryReceiveStream()


@pytest.mark.trio
async def test_factory_start_success():
    mock_protocol_class = mock.Mock()
    client = TrioModbusTcpClient(
        protocol_class=mock_protocol_class,
        host=mock.sentinel.HOST,
        port=mock.sentinel.PORT,
    )

    with mock.patch('trio.open_tcp_stream', new=mock.Mock(return_value=aag())) as patch:
        async with client.manage_connection():
            patch.assert_called_once_with(mock.sentinel.HOST, mock.sentinel.PORT)


@pytest.mark.parametrize("protocol", protocols)
def testClientProtocolConnectionMade(protocol):
    """
    Test the client protocol close
    :return:
    """
    protocol = protocol(ModbusSocketFramer(ClientDecoder()))
    transport = mock.Mock()
    protocol.connection_made(transport)
    assert protocol.transport == transport
    assert protocol._connected


@pytest.mark.trio
async def test_event_not_set(autojump_clock):
    event_and_value = _EventAndValue()
    with pytest.raises(trio.TooSlowError):
        with trio.fail_after(1):
            await event_and_value.event.wait()


def test_event_value_sentinel():
    event_and_value = _EventAndValue()
    assert event_and_value.value is event_and_value


@pytest.mark.trio
async def test_event_sets(autojump_clock):
    event_and_value = _EventAndValue()
    event_and_value.set(None)
    with trio.fail_after(1):
        await event_and_value.event.wait()


def test_event_holds_value():
    event_and_value = _EventAndValue()
    o = object()
    event_and_value.set(o)
    assert event_and_value.value is o


def test_protocol_build_packet_increments_tid():
    protocol = BaseModbusAsyncClientProtocol()
    requests = [
        ReadHoldingRegistersRequest(address=1, count=1) for _ in range(2)
    ]
    for request in requests:
        protocol._build_packet(request=request)
    assert requests[0].transaction_id + 1 == requests[1].transaction_id


def test_protocol_build_packet_packs_id():
    protocol = BaseModbusAsyncClientProtocol()
    unit_id = 0x23
    request = ReadHoldingRegistersRequest(address=1, count=1, unit=unit_id)
    packet = protocol._build_packet(request=request)
    assert packet[6] == unit_id


async def anoop():
    pass


@pytest.mark.trio
async def test_protocol_execute_sends():
    protocol = BaseModbusAsyncClientProtocol()
    transport = mock.Mock()
    transport.send_all = mock.Mock(return_value=anoop())
    protocol.transport = transport
    unit_id = 0x23
    request = ReadHoldingRegistersRequest(address=1, count=1, unit=unit_id)
    with pytest.raises(ConnectionException):
        await protocol.execute(request=request)
    expected_packet = b'\x00\x01\x00\x00\x00\x06\x23\x03\x00\x01\x00\x01'

    transport.send_all.assert_called_once_with(expected_packet)


def test_protocol_connection_made_saves_transport():
    protocol = BaseModbusAsyncClientProtocol()
    transport = object()
    protocol.connection_made(transport=transport)
    assert protocol.transport is transport


def test_protocol_connection_made_sets_connected():
    protocol = BaseModbusAsyncClientProtocol()
    protocol.connection_made(transport=object())
    assert protocol._connected


def test_protocol_connection_made_notifies_factory():
    protocol = BaseModbusAsyncClientProtocol()
    factory = mock.Mock()
    protocol.factory = factory
    protocol.connection_made(transport=object())
    factory.protocol_made_connection.assert_called_once_with(protocol)


def test_protocol_connection_lost():
    protocol = BaseModbusAsyncClientProtocol()
    tid = 3
    event_and_value = _EventAndValue()
    protocol.transaction.addTransaction(request=event_and_value, tid=tid)
    protocol._connectionLost('')
    assert event_and_value.event.is_set()
    with pytest.raises(ConnectionException):
        event_and_value.value.unwrap()


def test_protocol_data_received_processes():
    protocol = BaseModbusAsyncClientProtocol()
    protocol.framer.processIncomingPacket = mock.Mock()
    data = b'\x00\x01\x00\x00\x00\x05\x07\x03\x02\x9d\xdd'
    protocol._data_received(data)

    protocol.framer.processIncomingPacket.assert_called_once_with(
        data,
        protocol._handle_response,
        unit=7,
    )


def test_protocol_handle_response_skips_none_handler():
    protocol = BaseModbusAsyncClientProtocol()
    transaction_id = 13
    response = ReadHoldingRegistersResponse(
        values=[40412],
        transaction=transaction_id,
    )
    protocol.transaction.getTransaction = mock.Mock(return_value=None)

    protocol._handle_response(reply=response)

    protocol.transaction.getTransaction.assert_called_once_with(response.transaction_id)


def test_protocol_handle_response_calls_handler():
    protocol = BaseModbusAsyncClientProtocol()
    transaction_id = 13
    response = ReadHoldingRegistersResponse(
        values=[40412],
        transaction=transaction_id,
    )
    event_and_value = _EventAndValue()
    event_and_value.set = mock.Mock()
    protocol.transaction.getTransaction = mock.Mock(return_value=event_and_value)

    protocol._handle_response(reply=response)

    protocol.transaction.getTransaction.assert_called_once_with(response.transaction_id)
    event_and_value.set.assert_called_once_with(outcome.Value(response))


@pytest.mark.trio
async def test_protocol_build_response_raises_if_not_connected():
    protocol = BaseModbusAsyncClientProtocol()
    protocol._connected = False
    with pytest.raises(ConnectionException):
        await protocol._build_response(tid=None)


@pytest.mark.trio
async def test_protocol_build_response_adds_transaction(autojump_clock):
    protocol = BaseModbusAsyncClientProtocol()
    protocol._connected = True
    protocol.transaction.addTransaction = mock.Mock()
    transaction_id = 37
    with trio.move_on_after(1):
        await protocol._build_response(tid=transaction_id)

    protocol.transaction.addTransaction.assert_called_once()
    assert protocol.transaction.addTransaction.call_args.args[1] == transaction_id


@pytest.mark.trio
async def test_protocol_build_response_adds_transaction(autojump_clock):
    protocol = BaseModbusAsyncClientProtocol()
    protocol._connected = True
    transaction_id = 37
    value = 13
    event_and_value = _EventAndValue()
    event_and_value.set(outcome.Value(value))
    with trio.move_on_after(1):
        with mock.patch('pymodbus.client.asynchronous.trio._EventAndValue', return_value=event_and_value):
            result = await protocol._build_response(tid=transaction_id)

    assert result == value


def test_tcp_protocol_data_received():
    protocol = ModbusTcpClientProtocol()
    protocol._data_received = mock.Mock()
    data = object()
    protocol.data_received(data=data)
    protocol._data_received.assert_called_once_with(data)


@pytest.mark.trio
async def test_tcp_client_manage_connection_is_connected():
    client = TrioModbusTcpClient(host='127.0.0.1')
    with mock.patch('trio.open_tcp_stream', new=mock.Mock(return_value=aag())):
        async with client.manage_connection():
            assert client.connected


async def ag(iterable):
    for element in iterable:
        yield element


@pytest.mark.trio
async def test_client_receiver_passes_on_data():
    client = TrioModbusTcpClient()
    client.protocol = mock.Mock()
    client.protocol.data_received = mock.Mock()
    data = [1, 1, 2, 3, 5]
    await client._receiver(stream=ag(data))
    client.protocol.data_received.assert_has_calls(
        [mock.call(element) for element in data],
    )


def test_client_create_protocol():
    client = TrioModbusTcpClient(protocol_class=BaseModbusAsyncClientProtocol)
    protocol = client._create_protocol()
    assert isinstance(protocol, BaseModbusAsyncClientProtocol)
    assert protocol.factory is client


def test_client_protocol_made_connection():
    client = TrioModbusTcpClient()
    protocol = BaseModbusAsyncClientProtocol()
    client.protocol_made_connection(protocol=protocol)
    assert client.connected
    assert client.protocol is protocol


def test_client_protocol_remade_connection_ignore():
    client = TrioModbusTcpClient()
    protocol = BaseModbusAsyncClientProtocol()
    client.protocol_made_connection(protocol=protocol)
    client.protocol_made_connection(protocol=None)
    assert client.connected
    assert client.protocol is protocol


def test_init_tcp_client():
    client = init_tcp_client(host='127.0.0.1')
    assert isinstance(client, TrioModbusTcpClient)
