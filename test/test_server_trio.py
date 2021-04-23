import functools
import logging

import pytest
import trio

from pymodbus.client.asynchronous.schedulers import TRIO
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.datastore.context import ModbusServerContext, ModbusSlaveContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.pdu import ExceptionResponse, ModbusExceptions
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from pymodbus.server.trio import tcp_server
from pymodbus.register_write_message import WriteMultipleRegistersResponse


class RunningTrioServer:
    def __init__(self, context, host, port):
        self.context = context
        self.host = host
        self.port = port


@pytest.fixture(name="trio_server_context")
async def trio_server_context_fixture(request):
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
async def test_read_holding_registers(trio_tcp_client, trio_tcp_server):
    address = 12
    value = 40413
    # TODO: learn what fx is about...
    trio_tcp_server.context[0].setValues(
        fx=3,
        address=address,
        values=[value - 5, value, value + 5],
    )
    # TODO: is the +1 good?  seems related to ModbusSlaveContext.zero_mode probably
    response = await trio_tcp_client.read_holding_registers(
        address=address + 1,
        count=1,
    )
    assert isinstance(response, ReadHoldingRegistersResponse)
    assert response.registers == [value]


@pytest.mark.trio
async def test_write_holding_registers(trio_tcp_client, trio_tcp_server):
    address = 12
    value = 40413

    # TODO: is the +1 good?  seems related to ModbusSlaveContext.zero_mode probably
    response = await trio_tcp_client.write_registers(
        address=address + 1,
        values=[value],
    )
    assert isinstance(response, WriteMultipleRegistersResponse)

    # TODO: learn what fx is about...
    server_values = trio_tcp_server.context[0].getValues(
        fx=3,
        address=address,
        count=3,
    )
    assert server_values == [0, value, 0]


@pytest.mark.trio
async def test_large_count_excepts(trio_tcp_client):
    response = await trio_tcp_client.read_holding_registers(
        address=0,
        count=300,
    )
    assert isinstance(response, ExceptionResponse)
    assert response.exception_code == ModbusExceptions.IllegalValue


@pytest.mark.trio
async def test_invalid_client_excepts_gateway_no_response(trio_tcp_client):
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
async def test_logs_server_response_send(trio_tcp_client, caplog):
    with caplog.at_level(logging.DEBUG):
        await trio_tcp_client.read_holding_registers(address=0, count=1)

    assert "send: [ReadHoldingRegistersResponse (1)]- b'0001000000050003020000'" in caplog.text
