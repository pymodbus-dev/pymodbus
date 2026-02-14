"""Test server asyncio."""
from unittest import mock

import pytest

from pymodbus.datastore import ModbusServerContext
from pymodbus.framer import FramerType
from pymodbus.pdu import ReadHoldingRegistersRequest
from pymodbus.server import ModbusBaseServer
from pymodbus.simulator import SimData, SimDevice
from pymodbus.transport import CommParams, CommType


class TestBaseServer:
    """Test for the pymodbus.server.startstop module."""

    @pytest.fixture
    async def baseserver(self):
        """Fixture to provide base_server."""
        server = ModbusBaseServer(
            CommParams(
                comm_type=CommType.TCP,
                comm_name="server_listener",
                reconnect_delay=0.0,
                reconnect_delay_max=0.0,
                timeout_connect=0.0,
            ),
            ModbusServerContext(),
            False,
            False,
            None,
            FramerType.SOCKET,
            None,
            None,
            None,
            [ReadHoldingRegistersRequest],
        )
        return server

    async def test_base(self, baseserver):
        """Test __init__."""

    async def test_base_simcore(self):
        """Test __init___ with SimCore."""
        ModbusBaseServer(
            CommParams(
                comm_type=CommType.TCP,
                comm_name="server_listener",
                reconnect_delay=0.0,
                reconnect_delay_max=0.0,
                timeout_connect=0.0,
            ),
            SimDevice(0, SimData(0)),
            False,
            False,
            None,
            FramerType.SOCKET,
            None,
            None,
            None,
            [ReadHoldingRegistersRequest],
        )

    async def test_base_serve_forever1(self, baseserver):
        """Test serve_forever."""
        baseserver.listen = mock.AsyncMock(return_value=None)
        with pytest.raises(RuntimeError):
            await baseserver.serve_forever()

    async def test_base_serve_forever2(self, baseserver):
        """Test serve_forever."""
        baseserver.listen = mock.AsyncMock(return_value=True)
        await baseserver.serve_forever(background=True)
        baseserver.serving.set_result(True)
        await baseserver.serve_forever()


    async def test_base_connected(self, baseserver):
        """Test serve_forever."""
        with pytest.raises(RuntimeError):
            baseserver.callback_connected()

    async def test_base_disconnected(self, baseserver):
        """Test serve_forever."""
        with pytest.raises(RuntimeError):
            baseserver.callback_disconnected(None)

    async def test_base_data(self, baseserver):
        """Test serve_forever."""
        with pytest.raises(RuntimeError):
            baseserver.callback_data(None)
