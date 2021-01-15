import functools

import pytest
import trio

from pymodbus.client.asynchronous.schedulers import TRIO
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.datastore.context import ModbusServerContext, ModbusSlaveContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from pymodbus.server.trio import tcp_server


class RunningTrioServer:
    def __init__(self, context, host, port):
        self.context = context
        self.host = host
        self.port = port


@pytest.fixture(name="trio_tcp_server")
async def trio_tcp_server_fixture(nursery):
    host = "127.0.0.1"

    slave_context = ModbusSlaveContext()
    server_context = ModbusServerContext(slaves=slave_context)
    identity = ModbusDeviceIdentification()

    [listener] = await nursery.start(
        functools.partial(
            trio.serve_tcp,
            functools.partial(
                tcp_server,
                context=server_context,
                identity=identity,
            ),
            host=host,
            port=0,
        ),
    )

    yield RunningTrioServer(
        context=server_context, host=host, port=listener.socket.getsockname()[1]
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
    # TODO: learn what fx is about...
    trio_tcp_server.context[0].setValues(fx=3, address=12, values=[40312, 40413, 40514])
    response = await trio_tcp_client.read_holding_registers(address=13, count=1)
    assert isinstance(response, ReadHoldingRegistersResponse)
    assert response.registers == [40413]
