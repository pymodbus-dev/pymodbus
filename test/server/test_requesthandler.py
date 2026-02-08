"""Test server asyncio."""
from unittest import mock

import pytest

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.exceptions import ModbusIOException, NoSuchIdException
from pymodbus.framer import FramerType
from pymodbus.pdu import ExceptionResponse
from pymodbus.server import ModbusBaseServer, ModbusSerialServer
from pymodbus.transport import CommParams, CommType


class TestRequesthandler:
    """Test for the pymodbus.server.startstop module."""

    @pytest.fixture
    async def requesthandler(self):
        """Fixture to provide base_server."""
        store = ModbusDeviceContext(
            di=ModbusSequentialDataBlock(0, [17] * 100),
            co=ModbusSequentialDataBlock(0, [17] * 100),
            hr=ModbusSequentialDataBlock(0, [17] * 100),
            ir=ModbusSequentialDataBlock(0, [17] * 100),
        )
        server = ModbusBaseServer(
            CommParams(
                comm_type=CommType.TCP,
                comm_name="server_listener",
                reconnect_delay=0.0,
                reconnect_delay_max=0.0,
                timeout_connect=0.0,
                source_address=("0", 0),
            ),
            ModbusServerContext(devices=store, single=True),
            False,
            False,
            None,
            FramerType.SOCKET,
            None,
            None,
            None,
            [],
        )
        conn = server.callback_new_connection()
        conn.pdu_send = mock.Mock(return_value=True)
        return conn

    async def test_requesthandler(self, requesthandler):
        """Test __init__."""

    async def test_rh_callback_data(self, requesthandler):
        """Test __init__."""
        with mock.patch("pymodbus.transaction.TransactionManager.callback_data") as cb_data:
            cb_data.side_effect=ModbusIOException
            data = b"012"
            assert len(data) == requesthandler.callback_data(data, None)

    async def test_rh_handle_request(self, requesthandler):
        """Test __init__."""
        requesthandler.last_pdu = None
        await requesthandler.handle_request()
        requesthandler.last_pdu = ExceptionResponse(17)
        await requesthandler.handle_request()
        requesthandler.last_pdu.datastore_update = mock.AsyncMock()
        requesthandler.server.broadcast_enable = True
        requesthandler.last_pdu.dev_id = 0
        await requesthandler.handle_request()
        requesthandler.last_pdu.datastore_update.side_effect = NoSuchIdException
        await requesthandler.handle_request()
        requesthandler.server.ignore_missing_devices = True
        await requesthandler.handle_request()

    async def test_rh_server_send(self, requesthandler):
        """Test __init__."""
        requesthandler.server_send(None, None)
        requesthandler.server_send(ExceptionResponse(17), None)


    async def test_serial_server_allow_multiple(self):
        """Test __init__."""
        store = ModbusDeviceContext(
            di=ModbusSequentialDataBlock(0, [17] * 100),
            co=ModbusSequentialDataBlock(0, [17] * 100),
            hr=ModbusSequentialDataBlock(0, [17] * 100),
            ir=ModbusSequentialDataBlock(0, [17] * 100),
        )
        server = ModbusSerialServer(
            ModbusServerContext(devices=store, single=True),
            framer=FramerType.RTU,
            baudrate=19200,
            port="/dev/tty01",
            allow_multiple_devices=True,
        )
        server.callback_new_connection()

