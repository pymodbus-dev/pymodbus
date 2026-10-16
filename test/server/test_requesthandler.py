"""Test server asyncio."""

import asyncio
from unittest import mock

import pytest

from pymodbus.exceptions import ModbusIOException, NoSuchIdException
from pymodbus.framer import FramerType
from pymodbus.pdu import PDUexception
from pymodbus.server import ModbusBaseServer
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
            data = b"012"
            data_len = len(data)
            cb_data.side_effect = ModbusIOException(used_len=data_len)
            assert data_len == requesthandler.callback_data(data, None)

    async def test_rh_callback_data_undecodable_echoes_identity(self, requesthandler):
        """Undecodable FC exception must echo framing tid/dev_id (#2990)."""
        peer = ("192.0.2.1", 5020)
        with mock.patch(
            "pymodbus.transaction.TransactionManager.callback_data"
        ) as cb_data:
            data = b"\x00\x0a\x00\x00\x00\x06\x07\x0a\x00\x00\x00\x01"
            data_len = len(data)
            exc = ModbusIOException(
                "Unable to decode request",
                transaction_id=0x000A,
                dev_id=7,
                used_len=data_len,
            )
            cb_data.side_effect = exc
            assert data_len == requesthandler.callback_data(data, peer)

        requesthandler.pdu_send.assert_called_once()
        response = requesthandler.pdu_send.call_args.args[0]
        assert isinstance(response, PDUexception)
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
            data = b"garbage"
            data_len = len(data)
            cb_data.side_effect = ModbusIOException(
                "Unable to decode request", used_len=data_len
            )
            assert data_len == requesthandler.callback_data(data, None)

        response = requesthandler.pdu_send.call_args.args[0]
        assert response.transaction_id == 0
        assert response.dev_id == 0
        assert response.function_code == 0x80

    async def test_rh_callback_data_undecodable_real_socket_frame(self, requesthandler):
        """End-to-end: undecodable socket FC echoes MBAP transaction id."""
        # MBAP: tid=0x1234, pid=0, len=6, uid=1, PDU: FC=0x09 + 4 data bytes
        frame = b"\x12\x34\x00\x00\x00\x06\x01\x09\x00\x00\x00\x01"
        assert len(frame) == requesthandler.callback_data(frame, None)
        await asyncio.sleep(0.1)
        requesthandler.pdu_send.assert_called_once()
        response = requesthandler.pdu_send.call_args.args[0]
        assert isinstance(response, PDUexception)
        assert response.function_code == 0x80
        assert response.exception_code == 0x01
        assert not response.transaction_id
        assert not response.dev_id

    @pytest.mark.parametrize(
        ("data", "exp_len", "exp_send"),
        [
            (bytes.fromhex("000100000006010300000002"), 12, 1),
            (bytes.fromhex("000200000006010300100001"), 12, 1),
            (bytes.fromhex("000100000006010300000002000200000006010300100001"), 24, 2),
            (bytes.fromhex("0001000000060103000000020002"), 12, 1),
            (bytes.fromhex("000100000006016300000002"), 12, 1),
            (bytes.fromhex("000200000006010300100001000100000006016300000002"), 24, 2),
        ],
    )
    async def test_rh_callback_multi_frame(
        self, requesthandler, data, exp_len, exp_send
    ):
        """Test data can contain multiple frames."""
        assert exp_len == requesthandler.callback_data(data, None)
        await asyncio.sleep(0.1)
        assert exp_send == requesthandler.pdu_send.call_count

    @pytest.mark.parametrize(
        "second",
        [
            "000200000006000300000001",  # valid request
            "000200000006004100000001",  # unknown function code 0x41
        ],
    )
    async def test_rh_reply_goes_to_request_sender(self, requesthandler, second):
        """Each reply goes to the peer that sent its request.

        A UDP server shares one handler between all peers, so a second
        datagram can arrive before the first request is answered.
        """
        peer_a = ("192.0.2.1", 5020)
        peer_b = ("192.0.2.2", 5020)
        requesthandler.callback_data(bytes.fromhex("000100000006000300000001"), peer_a)
        requesthandler.callback_data(bytes.fromhex(second), peer_b)
        await asyncio.sleep(0.1)
        sent = {
            call.args[0].transaction_id: call.kwargs["addr"]
            for call in requesthandler.pdu_send.call_args_list
        }
        assert sent == {1: peer_a, 2: peer_b}

    async def test_rh_callback_exc(
        self,
        requesthandler,
    ):
        """Test exception response contains 0x80 + fc."""
        data = bytes.fromhex("000100000006014100000002")
        assert len(data) == requesthandler.callback_data(data, None)
        await asyncio.sleep(0.1)
        response = requesthandler.pdu_send.call_args.args[0]
        assert isinstance(response, PDUexception)
        assert response.function_code == 0x80
        assert response.exception_code == 0x01
        assert not response.transaction_id
        assert not response.dev_id

    async def test_rh_handle_request(self, requesthandler):
        """Test __init__."""
        requesthandler.last_pdu = PDUexception(0, 17, 0)
        await requesthandler.handle_request(requesthandler.last_pdu)
        requesthandler.last_pdu.build_response = mock.AsyncMock()  # type: ignore[method-assign]
        requesthandler.server.broadcast_enable = True
        requesthandler.last_pdu.dev_id = 0
        await requesthandler.handle_request(requesthandler.last_pdu)
        requesthandler.last_pdu.build_response.side_effect = NoSuchIdException
        await requesthandler.handle_request(requesthandler.last_pdu)
        requesthandler.server.ignore_missing_devices = True
        await requesthandler.handle_request(requesthandler.last_pdu)

    async def test_rh_server_send(self, requesthandler):
        """Test __init__."""
        requesthandler.server_send(None, None)
        requesthandler.server_send(PDUexception(0, 17, 0), None)
