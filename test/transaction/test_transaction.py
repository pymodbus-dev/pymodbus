"""Test transaction."""
import asyncio
from unittest import mock

import pytest

from pymodbus.client import ModbusBaseSyncClient
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.framer import FramerRTU, FramerSocket, FramerType
from pymodbus.pdu import DecodePDU, ExceptionResponse
from pymodbus.pdu.bit_message import ReadCoilsRequest, ReadCoilsResponse
from pymodbus.transaction import TransactionManager


@pytest.mark.parametrize("use_port", [5098])
class TestTransaction:
    """Test the pymodbus.transaction module."""

    async def test_transaction_instance(self, use_clc):
        """Test instantiate class."""
        TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(True)),
            5,
            True,
            None,
            None,
            None,
        )

    async def test_transaction_manager_tid(self, use_clc):
        """Test next TID."""
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        assert transact.getNextTID() == 1
        for tid in range(2, 12):
            assert tid == transact.getNextTID()
        assert transact.getNextTID() == 12
        transact.next_tid = 64999
        assert transact.getNextTID() == 65000
        assert transact.getNextTID() == 1

    async def test_transaction_calls(self, use_clc):
        """Test dummy calls from transport."""
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.callback_new_connection()
        transact.callback_connected()

    async def test_transaction_sync_pdu_send(self, use_clc):
        """Test dummy calls from transport."""
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.is_sync = True
        transact.comm_params.handle_local_echo = True
        transact.pdu_send(ExceptionResponse(0xff), (0,0))
        assert transact.sent_buffer == b'\x01\xff\x00a\xf0'

    async def test_transaction_disconnect(self, use_clc):
        """Test tracers in disconnect."""
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.trace_packet = mock.Mock()
        transact.trace_pdu = mock.Mock()
        transact.trace_connect = mock.Mock()
        transact.callback_disconnected(None)
        transact.trace_connect.assert_called_once_with(False)
        transact.trace_packet.assert_not_called()
        transact.trace_pdu.assert_not_called()

    @pytest.mark.parametrize(("test", "is_server"), [(True, False), (False, False), (True, True)])
    async def test_transaction_data(self, use_clc, test, is_server):
        """Test tracers in disconnect."""
        pdu = ExceptionResponse(0xff)
        pdu.dev_id = 0
        packet = b'\x00\x03\x00\x7c\x00\x02\x04\x02'
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.is_server = is_server
        transact.framer.processIncomingFrame = mock.Mock(return_value=(0, None))
        transact.callback_data(packet)
        assert not transact.response_future.done()

        if test:
            transact.trace_packet = mock.Mock(return_value=packet)
            transact.framer.processIncomingFrame.return_value = (1, pdu)
            transact.callback_data(packet)
            transact.trace_packet.assert_called_once_with(False, packet)
        else:
            transact.trace_packet = mock.Mock(return_value=packet)
            transact.trace_pdu = mock.Mock(return_value=pdu)
            transact.framer.processIncomingFrame.return_value = (1, pdu)
            transact.callback_data(packet)
            transact.trace_packet.assert_called_with(False, packet)
            transact.trace_pdu.assert_called_once_with(False, pdu)
            assert transact.response_future.result() == pdu

    @pytest.mark.parametrize("test", [True, False])
    async def test_transaction_data_2(self, use_clc, test):
        """Test tracers in disconnect."""
        pdu = ExceptionResponse(0xff)
        packet = b'\x00\x03\x00\x7c\x00\x02\x04\x02'
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.framer.processIncomingFrame = mock.Mock()
        transact.trace_packet = mock.Mock(return_value=packet)
        transact.framer.processIncomingFrame.return_value = (1, pdu)
        if test:
            pdu.dev_id = 17
        else:
            pdu.dev_id = 0
            transact.response_future.set_result((1, pdu))
        with pytest.raises(ModbusIOException):
            transact.callback_data(packet)

    @pytest.mark.parametrize("scenario", range(8))
    async def test_transaction_execute(self, use_clc, scenario):
        """Test tracers in disconnect."""
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.send = mock.Mock()
        request = ReadCoilsRequest(address=117, count=5, dev_id=1)
        response = ReadCoilsResponse(bits=[True, False, True, True, False], dev_id=1)
        transact.retries = 0
        transact.connection_made(mock.AsyncMock())
        transact.transport.write = mock.Mock()
        if scenario == 0: # transport not ok and no connect
            transact.transport = None
            with pytest.raises(ConnectionException):
                await transact.execute(False, request)
        elif scenario == 1: # transport not ok and connect, no trace
            transact.transport = None
            transact.connect = mock.AsyncMock(return_value=1)
            await transact.execute(True, request)
        elif scenario == 2: # transport ok, trace and send
            transact.trace_pdu = mock.Mock(return_value=request)
            transact.trace_packet = mock.Mock(return_value=b'123')
            await transact.execute(True, request)
            transact.trace_pdu.assert_called_once_with(True, request)
            transact.trace_packet.assert_called_once_with(True, b'\x01\x01\x00u\x00\x05\xed\xd3')
        elif scenario == 3: # wait receive,timeout, no_responses
            transact.comm_params.timeout_connect = 0.1
            transact.count_no_responses = 10
            transact.connection_lost = mock.Mock()
            with pytest.raises(ModbusIOException):
                await transact.execute(False, request)
        elif scenario == 4: # wait receive,timeout, disconnect
            transact.comm_params.timeout_connect = 0.1
            transact.count_no_responses = 10
            transact.count_until_disconnect = -1
            transact.connection_lost = mock.Mock()
            with pytest.raises(ModbusIOException):
                await transact.execute(False, request)
        elif scenario == 5: # wait receive,timeout, no_responses pass
            transact.comm_params.timeout_connect = 0.1
            transact.connection_lost = mock.Mock()
            with pytest.raises(ModbusIOException):
                await transact.execute(False, request)
        elif scenario == 6: # wait receive, cancel
            transact.comm_params.timeout_connect = 0.2
            resp = asyncio.create_task(transact.execute(False, request))
            await asyncio.sleep(0.1)
            resp.cancel()
            await asyncio.sleep(0.1)
            with pytest.raises(ModbusIOException):
                await resp
        else: # if scenario == 7: # response
            transact.comm_params.timeout_connect = 0.2
            resp = asyncio.create_task(transact.execute(False, request))
            await asyncio.sleep(0.1)
            transact.response_future.set_result(response)
            await asyncio.sleep(0.1)
            assert response == await resp

    async def test_transaction_receiver(self, use_clc):
        """Test tracers in disconnect."""
        transact = TransactionManager(
            use_clc,
            FramerSocket(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.send = mock.Mock()
        response = ReadCoilsResponse(bits=[True, False, True, True, False], dev_id=0)
        transact.retries = 0
        transact.connection_made(mock.AsyncMock())

        data = b"\x00\x00\x12\x34\x00\x06\x00\x01\x01\x02\x00\x04"
        transact.data_received(data)
        response = await transact.response_future
        assert isinstance(response, ReadCoilsResponse)

    @pytest.mark.parametrize("no_resp", [False, True])
    async def test_client_protocol_execute_outside(self, use_clc, no_resp):
        """Test the transaction execute method."""
        transact = TransactionManager(
            use_clc,
            FramerSocket(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.send = mock.Mock()
        request = ReadCoilsRequest(address=117, count=5, dev_id=1)
        transact.retries = 0
        transact.connection_made(mock.AsyncMock())
        transact.transport.write = mock.Mock()
        resp = asyncio.create_task(transact.execute(no_resp, request))
        await asyncio.sleep(0.2)
        data = b"\x00\x00\x12\x34\x00\x06\x01\x01\x01\x02\x00\x04"
        transact.data_received(data)
        result = await resp
        if no_resp:
            assert result.isError()
            assert isinstance(result, ExceptionResponse)
        else:
            assert not result.isError()
            assert isinstance(result, ReadCoilsResponse)

    async def test_transaction_id0(self, use_clc):
        """Test tracers in disconnect."""
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
        transact.send = mock.Mock()
        request = ReadCoilsRequest(address=117, count=5, dev_id=1)
        response = ReadCoilsResponse(bits=[True, False, True, True, False], dev_id=0)
        transact.retries = 0
        transact.connection_made(mock.AsyncMock())
        transact.transport.write = mock.Mock()
        transact.comm_params.timeout_connect = 0.2
        resp = asyncio.create_task(transact.execute(False, request))
        await asyncio.sleep(0.1)
        transact.response_future.set_result(response)
        await asyncio.sleep(0.1)
        with pytest.raises(ModbusIOException):
            await resp
        response = ReadCoilsResponse(bits=[True, False, True, True, False], dev_id=1)
        transact.retries = 0
        transact.connection_made(mock.AsyncMock())
        transact.transport.write = mock.Mock()
        transact.comm_params.timeout_connect = 0.2
        resp = asyncio.create_task(transact.execute(False, request))
        await asyncio.sleep(0.1)
        transact.response_future.set_result(response)
        await asyncio.sleep(0.1)
        assert response == await resp

    async def test_delayed_response(self, use_clc):
        """Test delayed response combined with retries."""
        _ = use_clc

@pytest.mark.parametrize("use_port", [5098])
class TestSyncTransaction:
    """Test the pymodbus.transaction module."""

    def test_sync_transaction_instance(self, use_clc):
        """Test instantiate class."""
        client = ModbusBaseSyncClient(
            FramerType.SOCKET,
            5,
            use_clc,
            None,
            None,
            None,
            )
        TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(True)),
            5,
            True,
            None,
            None,
            None,
            sync_client=client,
        )


    @pytest.mark.parametrize("scenario", range(7))
    async def test_sync_transaction_execute(self, use_clc, scenario):
        """Test tracers in disconnect."""
        client = ModbusBaseSyncClient(
            FramerType.SOCKET,
            5,
            use_clc,
            None,
            None,
            None,
            )
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        transact.send = mock.Mock()
        transact.sync_client.connect = mock.Mock(return_value=True)
        request = ReadCoilsRequest(address=117, count=5, dev_id=1)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False], dev_id=1)
        transact.retries = 0
        if scenario == 0: # transport not ok and no connect
            transact.transport = None
            transact.sync_client.connect = mock.Mock(return_value=False)
            with pytest.raises(ConnectionException):
                transact.sync_execute(False, request)
        elif scenario == 1: # transport not ok and connect, no trace
            transact.transport = None
            transact.sync_client.connect = mock.Mock(return_value=True)
            transact.sync_execute(True, request)
        elif scenario == 2: # transport ok, trace and send
            transact.trace_pdu = mock.Mock(return_value=request)
            transact.trace_packet = mock.Mock(return_value=b'123')
            transact.sync_execute(True, request)
            transact.trace_pdu.assert_called_once_with(True, request)
            transact.trace_packet.assert_called_once_with(True, b'\x01\x01\x00u\x00\x05\xed\xd3')
        elif scenario == 3: # wait receive,timeout, no_responses
            transact.comm_params.timeout_connect = 0.1
            transact.count_no_responses = 10
            with pytest.raises(ModbusIOException):
                transact.sync_execute(False, request)
        elif scenario == 4: # wait receive,timeout, disconnect
            transact.comm_params.timeout_connect = 0.1
            transact.count_no_responses = 10
            transact.count_until_disconnect = -1
            with pytest.raises(ModbusIOException):
                transact.sync_execute(False, request)
        elif scenario == 5: # wait receive,timeout, no_responses pass
            transact.comm_params.timeout_connect = 0.1
            with pytest.raises(ModbusIOException):
                transact.sync_execute(False, request)
        else: # if scenario == 6 # response
            transact.transport = 1
            resp_bytes = transact.framer.buildFrame(response)
            transact.sync_client.recv = mock.Mock(return_value=resp_bytes)
            transact.sync_client.send = mock.Mock()
            transact.comm_params.timeout_connect = 0.2
            resp = transact.sync_execute(False, request)
            assert response.bits == resp.bits

    def test_sync_transaction_receiver(self, use_clc):
        """Test tracers in disconnect."""
        client = ModbusBaseSyncClient(
            FramerType.SOCKET,
            5,
            use_clc,
            None,
            None,
            None,
            )
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        transact.sync_client.connect = mock.Mock(return_value=True)
        transact.sync_client.send = mock.Mock()
        request = ReadCoilsRequest(address=117, count=5, dev_id=1)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False], dev_id=1)
        transact.retries = 0
        transact.transport = 1
        resp_bytes = transact.framer.buildFrame(response)
        transact.sync_client.recv = mock.Mock(return_value=resp_bytes)
        transact.sync_client.send = mock.Mock()
        transact.comm_params.timeout_connect = 0.2
        resp = transact.sync_execute(False, request)
        assert response.bits == resp.bits

    @pytest.mark.parametrize("no_resp", [False, True])
    def test_sync_client_protocol_execute_outside(self, use_clc, no_resp):
        """Test the transaction execute method."""
        client = ModbusBaseSyncClient(
            FramerType.SOCKET,
            5,
            use_clc,
            None,
            None,
            None,
        )
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        transact.sync_client.connect = mock.Mock(return_value=True)
        request = ReadCoilsRequest(address=117, count=5, dev_id=1)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False], dev_id=1)
        transact.retries = 0
        transact.transport = 1
        resp_bytes = transact.framer.buildFrame(response)
        transact.sync_client.recv = mock.Mock(return_value=resp_bytes)
        transact.sync_client.send = mock.Mock()
        result = transact.sync_execute(no_resp, request)
        if no_resp:
            assert result.isError()
        else:
            assert not result.isError()
            assert isinstance(response, ReadCoilsResponse)

    def test_sync_client_protocol_execute_no_pdu(self, use_clc):
        """Test the transaction execute method."""
        client = ModbusBaseSyncClient(
            FramerType.SOCKET,
            5,
            use_clc,
            None,
            None,
            None,
        )
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        transact.sync_client.connect = mock.Mock(return_value=True)
        request = ReadCoilsRequest(address=117, count=5, dev_id=1)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False], dev_id=1)
        transact.retries = 0
        transact.transport = 1
        resp_bytes = transact.framer.buildFrame(response)[:-1]
        transact.sync_client.recv = mock.Mock(side_effect=[resp_bytes, b''])
        transact.sync_client.send = mock.Mock()
        with pytest.raises(ModbusIOException):
            transact.sync_execute(False, request)

    def test_transaction_sync_id0(self, use_clc):
        """Test id 0 in sync."""
        client = ModbusBaseSyncClient(
            FramerType.SOCKET,
            5,
            use_clc,
            None,
            None,
            None,
            )
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        transact.sync_client.connect = mock.Mock(return_value=True)
        transact.sync_client.send = mock.Mock()
        request = ReadCoilsRequest(address=117, count=5, dev_id=0)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False], dev_id=1)
        transact.retries = 0
        transact.transport = 1
        resp_bytes = transact.framer.buildFrame(response)
        transact.sync_client.recv = mock.Mock(return_value=resp_bytes)
        transact.sync_client.send = mock.Mock()
        transact.comm_params.timeout_connect = 0.2
        with pytest.raises(ModbusIOException):
            transact.sync_execute(False, request)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False], dev_id=0)
        resp_bytes = transact.framer.buildFrame(response)
        transact.sync_client.recv = mock.Mock(return_value=resp_bytes)
        resp = transact.sync_execute(False, request)
        assert not resp.isError()

    def test_transaction_sync_get_response(self, use_clc):
        """Test id 0 in sync."""
        client = ModbusBaseSyncClient(
            FramerType.SOCKET,
            5,
            use_clc,
            None,
            None,
            None,
            )
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        client.recv = mock.Mock()
        request = transact.framer.buildFrame(ReadCoilsRequest(address=117, count=5, dev_id=1))
        response = transact.framer.buildFrame(ReadCoilsResponse(bits=[True*8], dev_id=1))
        transact.sent_buffer = request
        client.recv.side_effect = [request, response]
        pdu = transact.sync_get_response(1)
        assert isinstance(pdu, ReadCoilsResponse)
        transact.sent_buffer = request
        client.recv.side_effect = [request[:3], request[3:], response]
        pdu = transact.sync_get_response(1)
        assert isinstance(pdu, ReadCoilsResponse)
        transact.sent_buffer = request
        client.recv.side_effect = [response]
        pdu = transact.sync_get_response(1)
        assert isinstance(pdu, ReadCoilsResponse)
