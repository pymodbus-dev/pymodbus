"""Test transaction."""
import asyncio
from unittest import mock

import pytest

from pymodbus.client import ModbusBaseSyncClient
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.framer import FramerRTU, FramerSocket, FramerType
from pymodbus.pdu import DecodePDU
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

    @pytest.mark.parametrize("test", [True, False])
    async def test_transaction_data(self, use_clc, test):
        """Test tracers in disconnect."""
        pdu = "dummy pdu"
        packet = b'123'
        transact = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            5,
            False,
            None,
            None,
            None,
        )
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

    @pytest.mark.parametrize("scenario", range(6))
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
        request = ReadCoilsRequest(address=117, count=5)
        response = ReadCoilsResponse(bits=[True, False, True, True, False])
        transact.retries = 0
        transact.connection_made(mock.AsyncMock())
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
            transact.trace_packet.assert_called_once_with(True, b'\x00\x01\x00u\x00\x05\xec\x02')
        elif scenario == 3: # wait receive,timeout, no_responses
            transact.comm_params.timeout_connect = 0.1
            transact.count_no_responses = 10
            transact.connection_lost = mock.Mock()
            with pytest.raises(ModbusIOException):
                await transact.execute(False, request)
        elif scenario == 4: # wait receive,timeout, no_responses pass
            transact.comm_params.timeout_connect = 0.1
            transact.connection_lost = mock.Mock()
            assert not await transact.execute(False, request)
        else: # if scenario == 5: # response
            transact.comm_params.timeout_connect = 0.2
            transact.response_future.set_result(response)
            resp = asyncio.create_task(transact.execute(False, request))
            await asyncio.sleep(0.2)
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
        response = ReadCoilsResponse(bits=[True, False, True, True, False])
        transact.retries = 0
        transact.connection_made(mock.AsyncMock())

        data = b"\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04"
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
        request = ReadCoilsRequest(address=117, count=5)
        transact.retries = 0
        transact.connection_made(mock.AsyncMock())
        resp = asyncio.create_task(transact.execute(no_resp, request))
        await asyncio.sleep(0.2)
        data = b"\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04"
        transact.data_received(data)
        result = await resp
        if no_resp:
            assert not result
        else:
            assert not result.isError()
            assert isinstance(result, ReadCoilsResponse)


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


    @pytest.mark.parametrize("scenario", range(6))
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
        request = ReadCoilsRequest(address=117, count=5)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False])
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
            transact.trace_packet.assert_called_once_with(True, b'\x00\x01\x00u\x00\x05\xec\x02')
        elif scenario == 3: # wait receive,timeout, no_responses
            transact.comm_params.timeout_connect = 0.1
            transact.count_no_responses = 10
            with pytest.raises(ModbusIOException):
                transact.sync_execute(False, request)
        elif scenario == 4: # wait receive,timeout, no_responses pass
            transact.comm_params.timeout_connect = 0.1
            with pytest.raises(ModbusIOException):
                transact.sync_execute(False, request)
        else: # if scenario == 5 # response
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
        transact.sync_client.send = mock.Mock()
        request = ReadCoilsRequest(address=117, count=5)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False])
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
        request = ReadCoilsRequest(address=117, count=5)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False])
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
        request = ReadCoilsRequest(address=117, count=5)
        response = ReadCoilsResponse(bits=[True, False, True, True, False, False, False, False])
        transact.retries = 0
        transact.transport = 1
        resp_bytes = transact.framer.buildFrame(response)[:-1]
        transact.sync_client.recv = mock.Mock(side_effect=[resp_bytes, b''])
        transact.sync_client.send = mock.Mock()
        with pytest.raises(ModbusIOException):
            transact.sync_execute(False, request)
