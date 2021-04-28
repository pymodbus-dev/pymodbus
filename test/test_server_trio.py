from unittest import mock

import functools
import logging

import pytest
import trio

from pymodbus.client.asynchronous.schedulers import TRIO
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.datastore.context import ModbusServerContext, ModbusSlaveContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.factory import ServerDecoder
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.pdu import ExceptionResponse, ModbusExceptions
from pymodbus.register_read_message import (
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
)
from pymodbus.server.trio import Executor, incoming, tcp_server
from pymodbus.register_write_message import WriteMultipleRegistersResponse


class RunningTrioServer:
    def __init__(self, context, host, port):
        self.context = context
        self.host = host
        self.port = port


@pytest.fixture(name="trio_server_context")
def trio_server_context_fixture(request):
    node = request.node
    single = node.get_closest_marker("single")
    no_contexts = node.get_closest_marker("no_contexts")

    if no_contexts:
        slaves = {}
    else:
        slave_context = ModbusSlaveContext()

        if single:
            slaves = slave_context
        else:
            slaves = {0: slave_context}

    server_context = ModbusServerContext(slaves=slaves, single=single)

    return server_context


@pytest.fixture(name="trio_server_multiunit_context")
def trio_server_multiunit_context_fixture(request):
    slaves = {i: ModbusSlaveContext() for i in range(3)}

    server_context = ModbusServerContext(slaves=slaves, single=False)

    return server_context


@pytest.fixture(name="trio_tcp_server")
async def trio_tcp_server_fixture(request, nursery, trio_server_context):
    node = request.node
    broadcast_enable = node.get_closest_marker("broadcast_enable")
    ignore_missing_slaves = node.get_closest_marker("ignore_missing_slaves")

    host = "127.0.0.1"

    identity = ModbusDeviceIdentification()

    [listener] = await nursery.start(
        functools.partial(
            trio.serve_tcp,
            functools.partial(
                tcp_server,
                context=trio_server_context,
                identity=identity,
                ignore_missing_slaves=ignore_missing_slaves,
                broadcast_enable=broadcast_enable,
            ),
            host=host,
            port=0,
        ),
    )

    yield RunningTrioServer(
        context=trio_server_context,
        host=host,
        port=listener.socket.getsockname()[1],
    )


@pytest.fixture(name="trio_tcp_client")
async def trio_tcp_client_fixture(trio_tcp_server):
    modbus_client = AsyncModbusTCPClient(
        scheduler=TRIO,
        host=trio_tcp_server.host,
        port=trio_tcp_server.port,
    )

    async with modbus_client.manage_connection() as protocol:
        yield protocol


@pytest.mark.trio
async def test_read_holding_registers(trio_tcp_client, trio_tcp_server, autojump_clock):
    address = 12
    value = 40413
    trio_tcp_server.context[0].setValues(
        fx=3,
        address=address,
        values=[value - 5, value, value + 5],
    )
    response = await trio_tcp_client.read_holding_registers(
        # plus one for since the address is the beginning of the three values
        address=address + 1,
        count=1,
    )
    assert isinstance(response, ReadHoldingRegistersResponse)
    assert response.registers == [value]


@pytest.mark.trio
async def test_write_holding_registers(trio_tcp_client, trio_tcp_server, autojump_clock):
    address = 12
    value = 40413

    response = await trio_tcp_client.write_registers(
        # plus one for since the address is the beginning of the three values
        address=address + 1,
        values=[value],
    )
    assert isinstance(response, WriteMultipleRegistersResponse)

    server_values = trio_tcp_server.context[0].getValues(
        fx=3,
        address=address,
        count=3,
    )
    assert server_values == [0, value, 0]


@pytest.mark.trio
async def test_large_count_excepts(trio_tcp_client, autojump_clock):
    response = await trio_tcp_client.read_holding_registers(
        address=0,
        count=300,
    )
    assert isinstance(response, ExceptionResponse)
    assert response.exception_code == ModbusExceptions.IllegalValue


@pytest.mark.trio
async def test_invalid_client_excepts_gateway_no_response(trio_tcp_client, autojump_clock):
    response = await trio_tcp_client.read_holding_registers(
        address=0,
        count=1,
        unit=57,
    )
    assert isinstance(response, ExceptionResponse)
    assert response.exception_code == ModbusExceptions.GatewayNoResponse


@pytest.mark.ignore_missing_slaves
@pytest.mark.trio
async def test_invalid_unit_times_out_when_ignoring_missing_slaves(trio_tcp_client):
    with pytest.raises(trio.TooSlowError):
        await trio_tcp_client.read_holding_registers(
            address=0,
            count=1,
            unit=57,
        )


@pytest.mark.broadcast_enable
@pytest.mark.trio
async def test_times_out_when_broadcast_enabled(trio_tcp_client):
    with pytest.raises(trio.TooSlowError):
        await trio_tcp_client.read_holding_registers(
            address=0,
            count=1,
            unit=0,
        )


@pytest.mark.broadcast_enable
@pytest.mark.no_contexts
@pytest.mark.trio
async def test_times_out_when_broadcast_enabled_and_no_contexts(trio_tcp_client):
    with pytest.raises(trio.TooSlowError):
        await trio_tcp_client.read_holding_registers(
            address=0,
            count=1,
            unit=0,
        )


@pytest.mark.trio
async def test_logs_server_response_send(trio_tcp_client, caplog, autojump_clock):
    with caplog.at_level(logging.DEBUG):
        await trio_tcp_client.read_holding_registers(address=0, count=1)

    assert "send: [ReadHoldingRegistersResponse (1)]- b'0001000000050003020000'" in caplog.text


def test_execute_broadcasts(trio_server_multiunit_context):
    context = trio_server_multiunit_context
    response_send, response_receive = trio.open_memory_channel(max_buffer_size=1)

    test_request = ReadHoldingRegistersRequest(address=1, count=1, unit=0)
    test_request.execute = mock.Mock()
    test_request.doException = mock.Mock()
    executor = Executor(
        addr=None,
        context=context,
        response_send=response_send,
        ignore_missing_slaves=False,
        broadcast_enable=True,
    )
    executor.execute(request=test_request)

    test_request.execute.assert_has_calls([mock.call(v) for _, v in context])
    test_request.doException.assert_not_called()


@pytest.mark.parametrize(
    argnames=["unit_id", "broadcast_enabled"],
    argvalues=[[0, False], [1, True]],
)
def test_execute_does_not_broadcast(
    trio_server_multiunit_context,
    unit_id,
    broadcast_enabled,
):
    context = trio_server_multiunit_context
    response_send, response_receive = trio.open_memory_channel(max_buffer_size=1)

    test_request = ReadHoldingRegistersRequest(address=1, count=1, unit=unit_id)
    test_request.execute = mock.Mock()
    test_request.doException = mock.Mock()
    executor = Executor(
        addr=None,
        context=context,
        response_send=response_send,
        ignore_missing_slaves=False,
        broadcast_enable=broadcast_enabled,
    )
    executor.execute(request=test_request)

    slave_context = dict(context)[unit_id]

    test_request.execute.assert_called_with(slave_context)
    test_request.doException.assert_not_called()


def test_execute_does_ignore_missing_slaves(trio_server_multiunit_context):
    context = trio_server_multiunit_context

    missing_unit_id = max(context.slaves()) + 1

    test_request = ReadHoldingRegistersRequest(address=1, count=1, unit=missing_unit_id)
    test_request.execute = mock.Mock()
    test_request.doException = mock.Mock()
    executor = Executor(
        addr=None,
        context=context,
        response_send=None,
        ignore_missing_slaves=True,
        broadcast_enable=True,
    )
    executor.execute(request=test_request)

    test_request.execute.assert_not_called()
    test_request.doException.assert_not_called()


def test_execute_does_not_ignore_missing_slaves(trio_server_multiunit_context):
    context = trio_server_multiunit_context
    response_send, response_receive = trio.open_memory_channel(max_buffer_size=1)

    missing_unit_id = max(context.slaves()) + 1

    test_request = ReadHoldingRegistersRequest(address=1, count=1, unit=missing_unit_id)
    test_request.execute = mock.Mock()
    test_request.doException = mock.Mock()
    executor = Executor(
        addr=None,
        context=context,
        response_send=response_send,
        ignore_missing_slaves=False,
        broadcast_enable=True,
    )
    executor.execute(request=test_request)

    test_request.execute.assert_not_called()
    test_request.doException.assert_called_once_with(ModbusExceptions.GatewayNoResponse)


def test_execute_handles_slave_failure(trio_server_multiunit_context):
    context = trio_server_multiunit_context
    response_send, response_receive = trio.open_memory_channel(max_buffer_size=1)

    test_request = ReadHoldingRegistersRequest(address=1, count=1, unit=0)
    test_request.execute = mock.Mock(side_effect=Exception)
    test_request.doException = mock.Mock()
    executor = Executor(
        addr=None,
        context=context,
        response_send=response_send,
        ignore_missing_slaves=False,
        broadcast_enable=True,
    )
    executor.execute(request=test_request)

    test_request.execute.assert_called_once()
    test_request.doException.assert_called_once_with(ModbusExceptions.SlaveFailure)


@pytest.mark.trio
async def test_incoming_closes_response_send_channel(trio_server_context):
    server_send, server_receive = trio.open_memory_channel(max_buffer_size=1)
    response_send, response_receive = trio.open_memory_channel(max_buffer_size=1)

    server_send.close()

    await incoming(
        server_stream=server_receive,
        framer=None,
        context=trio_server_context,
        response_send=response_send,
        ignore_missing_slaves=None,
        broadcast_enable=None,
    )

    with pytest.raises(trio.ClosedResourceError):
        response_send.send_nowait(None)


sample_read_data = b'\x00\x01\x00\x00\x00\x06\x00\x03\x00\r\x00\x01'


@pytest.mark.trio
@pytest.mark.parametrize(
    argnames=['data_blocks'],
    argvalues=[
        [[sample_read_data]],
        # TODO: enable when the framer can handle fragmentation
        # [[sample_read_data[:5], sample_read_data[5:]]],
        # [[bytes([byte]) for byte in sample_read_data]],
    ],
)
async def test_incoming_processes(trio_server_context, data_blocks):
    server_send, server_receive = trio.open_memory_channel(
        max_buffer_size=len(data_blocks),
    )
    response_send, response_receive = trio.open_memory_channel(max_buffer_size=1)
    framer = ModbusSocketFramer(decoder=ServerDecoder(), client=None)

    with response_receive:
        with server_send:
            for block in data_blocks:
                server_send.send_nowait(block)

        await incoming(
            server_stream=server_receive,
            framer=framer,
            context=trio_server_context,
            response_send=response_send,
            ignore_missing_slaves=None,
            broadcast_enable=None,
        )

        responses = [response async for response in response_receive]

    assert len(responses) == 1
    [[response, address]] = responses
    assert isinstance(response, ReadHoldingRegistersResponse)
