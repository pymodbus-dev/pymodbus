"""Test server asyncio."""

from unittest import mock

import pytest

from pymodbus.exceptions import ModbusIOException, NoSuchIdException
from pymodbus.framer import FramerType
from pymodbus.pdu import ExceptionResponse
from pymodbus.server import ModbusBaseServer, ModbusSerialServer
from pymodbus.simulator import DataType, SimData, SimDevice
from pymodbus.transport import CommParams, CommType


class TestRequesthandler:
    """Test for the pymodbus.server.startstop module."""

    @pytest.fixture
    async def requesthandler(self):
        """Fixture to provide base_server."""
        server = ModbusBaseServer(
            CommParams(
                comm_type=CommType.TCP,
                comm_name="server_listener",
                reconnect_delay=0.0,
                reconnect_delay_max=0.0,
                timeout_connect=0.0,
                source_address=("0", 0),
            ),
            SimDevice(0, SimData(0, datatype=DataType.REGISTERS, values=[17] * 100)),
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
        conn.pdu_send = mock.Mock(return_value=True)  # type: ignore[method-assign]
        return conn

    async def test_requesthandler(self, requesthandler):
        """Test __init__."""

    async def test_rh_callback_data(self, requesthandler):
        """Test __init__."""
        with mock.patch(
            "pymodbus.transaction.TransactionManager.callback_data"
        ) as cb_data:
            cb_data.side_effect = ModbusIOException
            data = b"012"
            assert len(data) == requesthandler.callback_data(data, None)

    async def test_rh_callback_data_undecodable_echoes_identity(self, requesthandler):
        """Undecodable FC exception must echo framing tid/dev_id (#2990)."""
        peer = ("192.0.2.1", 5020)
        with mock.patch(
            "pymodbus.transaction.TransactionManager.callback_data"
        ) as cb_data:
            exc = ModbusIOException(
                "Unable to decode request",
                transaction_id=0x000A,
                dev_id=7,
            )
            cb_data.side_effect = exc
            data = b"\x00\x0a\x00\x00\x00\x06\x07\x0a\x00\x00\x00\x01"
            assert len(data) == requesthandler.callback_data(data, peer)

        requesthandler.pdu_send.assert_called_once()
        response = requesthandler.pdu_send.call_args.args[0]
        assert isinstance(response, ExceptionResponse)
        assert response.transaction_id == 0x000A
        assert response.dev_id == 7
        assert response.function_code == 0x80
        assert response.exception_code == 0x01
        assert requesthandler.pdu_send.call_args.kwargs.get("addr") == peer

    async def test_rh_callback_data_undecodable_without_framing_attrs(
        self, requesthandler
    ):
        """Missing framing attrs fall back to zeros rather than crashing."""
        with mock.patch(
            "pymodbus.transaction.TransactionManager.callback_data"
        ) as cb_data:
            cb_data.side_effect = ModbusIOException("Unable to decode request")
            data = b"garbage"
            assert len(data) == requesthandler.callback_data(data, None)

        response = requesthandler.pdu_send.call_args.args[0]
        assert response.transaction_id == 0
        assert response.dev_id == 0
        assert response.function_code == 0x80

    async def test_rh_callback_data_undecodable_real_socket_frame(self, requesthandler):
        """End-to-end: undecodable socket FC echoes MBAP transaction id."""
        # MBAP: tid=0x1234, pid=0, len=6, uid=1, PDU: FC=0x09 + 4 data bytes
        frame = b"\x12\x34\x00\x00\x00\x06\x01\x09\x00\x00\x00\x01"
        assert len(frame) == requesthandler.callback_data(frame, None)

        requesthandler.pdu_send.assert_called_once()
        response = requesthandler.pdu_send.call_args.args[0]
        assert isinstance(response, ExceptionResponse)
        assert response.transaction_id == 0x1234
        assert response.dev_id == 1
        assert response.function_code == 0x80
        assert response.exception_code == 0x01

    async def test_rh_handle_request(self, requesthandler):
        """Test __init__."""
        requesthandler.last_pdu = None
        await requesthandler.handle_request()
        requesthandler.last_pdu = ExceptionResponse(17)
        await requesthandler.handle_request()
        requesthandler.last_pdu.datastore_update = mock.AsyncMock()  # type: ignore[method-assign]
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
        server = ModbusSerialServer(
            SimDevice(0, SimData(0, datatype=DataType.REGISTERS, values=[17] * 100)),
            framer=FramerType.RTU,
            baudrate=19200,
            port="/dev/tty01",
            allow_multiple_devices=True,
        )
        server.callback_new_connection()
