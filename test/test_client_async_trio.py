from unittest import mock

import pytest
import trio

from pymodbus.client.asynchronous.trio import (
    _EventAndValue,
    BaseModbusAsyncClientProtocol,
    ModbusTcpClientProtocol,
    TrioModbusTcpClient,
)
from pymodbus.exceptions import ConnectionException
from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.register_read_message import ReadHoldingRegistersRequest
protocols = [ModbusTcpClientProtocol]


def test_factory_stop():
    mock_protocol_class = mock.MagicMock()
    client = TrioModbusTcpClient(protocol_class=mock_protocol_class)

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
    client = TrioModbusTcpClient(protocol_class=mock_protocol_class)

    assert not client.connected
    assert client.protocol is None
    client.protocol_made_connection(mock.sentinel.PROTOCOL)
    assert client.connected
    assert client.protocol is mock.sentinel.PROTOCOL

    client.protocol_made_connection(mock.sentinel.PROTOCOL_UNEXPECTED)
    assert client.connected
    assert client.protocol is mock.sentinel.PROTOCOL

# @pytest.mark.trio
# async def test_factory_start_success(self):
#     mock_protocol_class = mock.MagicMock()
#     client = TrioModbusTcpClient(
#         protocol_class=mock_protocol_class,
#         host=mock.sentinel.HOST,
#         port=mock.sentinel.PORT,
#     )
#
#     async with client.manage_connection():
#         # mock_loop.create_connection.assert_called_once_with(mock.ANY, mock.sentinel.HOST, mock.sentinel.PORT)
#         # assert mock_async.call_count == 0
#         pass

@pytest.mark.parametrize("protocol", protocols)
def testClientProtocolConnectionMade(protocol):
    """
    Test the client protocol close
    :return:
    """
    protocol = protocol(ModbusSocketFramer(ClientDecoder()))
    transport = mock.MagicMock()
    protocol.connection_made(transport)
    assert protocol.transport == transport
    # assert protocol.connected


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


@pytest.mark.trio
async def test_protocol_execute_sends():
    protocol = BaseModbusAsyncClientProtocol()
    transport = mock.AsyncMock()
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
    factory = mock.MagicMock()
    protocol.factory = factory
    protocol.connection_made(transport=object())
    factory.protocol_made_connection.assert_called_once_with(protocol)
