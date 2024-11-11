"""Test transaction."""
import asyncio
from unittest import mock

import pytest

from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.framer import FramerRTU
from pymodbus.pdu import DecodePDU
from pymodbus.pdu.bit_message import ReadCoilsRequest, ReadCoilsResponse
from pymodbus.transaction import TransactionManager


@pytest.mark.parametrize("use_port", [5098])
class TestTransaction:
    """Test the pymodbus.transaction module."""

    async def test_transaction_instance(self, use_clc):
        """Test instantiate class."""
        TransactionManager(use_clc, FramerRTU(DecodePDU(False)), 5, False)
        TransactionManager(use_clc, FramerRTU(DecodePDU(True)), 5, True)

    async def test_transaction_manager_tid(self, use_clc):
        """Test next TID."""
        transact = TransactionManager(use_clc, FramerRTU(DecodePDU(False)), 5, False)
        assert transact.getNextTID() == 1
        for tid in range(2, 12):
            assert tid == transact.getNextTID()
        assert transact.getNextTID() == 12
        transact.next_tid = 64999
        assert transact.getNextTID() == 65000
        assert transact.getNextTID() == 1

    async def test_transaction_calls(self, use_clc):
        """Test dummy calls from transport."""
        transact = TransactionManager(use_clc, FramerRTU(DecodePDU(False)), 5, False)
        transact.callback_new_connection()
        transact.callback_connected()

    async def test_transaction_disconnect(self, use_clc):
        """Test tracers in disconnect."""
        transact = TransactionManager(use_clc, FramerRTU(DecodePDU(False)), 5, False)
        transact.callback_disconnected(None)
        transact.trace_recv_packet = mock.Mock()
        transact.trace_recv_pdu = mock.Mock()
        transact.trace_send_packet = mock.Mock()
        transact.trace_send_pdu = mock.Mock()
        transact.callback_disconnected(None)
        transact.trace_recv_packet.assert_called_once_with(None)
        transact.trace_recv_pdu.assert_called_once_with(None)
        transact.trace_send_packet.assert_called_once_with(None)
        transact.trace_send_pdu.assert_called_once_with(None)

    @pytest.mark.parametrize("test", [True, False])
    async def test_transaction_data(self, use_clc, test):
        """Test tracers in disconnect."""
        transact = TransactionManager(use_clc, FramerRTU(DecodePDU(False)), 5, False)
        transact.framer.processIncomingFrame = mock.Mock(return_value=(0, None))
        packet = b'123'
        transact.callback_data(packet)
        assert not transact.response_future.done()
        transact.trace_recv_packet = mock.Mock()
        pdu = "dummy pdu"

        if test:
            transact.framer.processIncomingFrame.return_value = (1, pdu)
            transact.callback_data(packet)
            transact.trace_recv_packet.assert_called_once_with(packet)
        else:
            transact.trace_recv_pdu = mock.Mock(return_value=pdu)
            transact.framer.processIncomingFrame.return_value = (1, pdu)
            transact.callback_data(packet)
            transact.trace_recv_packet.assert_called_with(packet)
            transact.trace_recv_pdu.assert_called_once_with(pdu)
            assert transact.response_future.result() == pdu

    @pytest.mark.parametrize("scenario", range(7))
    async def test_transaction_execute(self, use_clc, scenario):
        """Test tracers in disconnect."""
        transact = TransactionManager(use_clc, FramerRTU(DecodePDU(False)), 5, False)
        transact.send = mock.Mock()
        request = ReadCoilsRequest(address=117, count=5)
        response = ReadCoilsResponse(bits=[True, False, True, True, False])
        transact.retries = 0
        transact.transport = 1
        if scenario == 0: # transport not ok and no connect
            transact.transport = None
            with pytest.raises(ConnectionException):
                await transact.execute(False, request)
        elif scenario == 2: # transport not ok and connect, no trace
            transact.transport = None
            transact.connect = mock.AsyncMock(return_value=1)
            await transact.execute(True, request)
        elif scenario == 3: # transport ok, trace and send
            transact.trace_send_pdu = mock.Mock(return_value=request)
            transact.trace_send_packet = mock.Mock(return_value=b'123')
            await transact.execute(True, request)
            transact.trace_send_pdu.assert_called_once_with(request)
            transact.trace_send_packet.assert_called_once_with(b'\x00\x01\x00u\x00\x05\xec\x02')
        elif scenario == 4: # wait receive,timeout, no_responses
            transact.comm_params.timeout_connect = 0.1
            transact.count_no_responses = 10
            transact.connection_lost = mock.Mock()
            with pytest.raises(ModbusIOException):
                await transact.execute(False, request)
        elif scenario == 5: # wait receive,timeout, no_responses pass
            transact.comm_params.timeout_connect = 0.1
            transact.connection_lost = mock.Mock()
            assert not await transact.execute(False, request)
        elif scenario == 6: # response
            transact.comm_params.timeout_connect = 0.2
            transact.response_future.set_result(response)
            resp = asyncio.create_task(transact.execute(False, request))
            await asyncio.sleep(0.2)
            assert response == await resp

