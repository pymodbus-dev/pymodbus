"""Test optional serial transaction spacing."""

import asyncio
import math
from itertools import pairwise
from time import monotonic, sleep
from unittest import mock

import pytest
import pytest_asyncio

import pymodbus.transaction.transaction as transaction_module
from pymodbus.client import AsyncModbusSerialClient, ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.framer import FramerRTU
from pymodbus.pdu import DecodePDU
from pymodbus.pdu.bit_message import ReadCoilsRequest, ReadCoilsResponse
from pymodbus.transaction import TransactionManager
from pymodbus.transport import CommType


@pytest.mark.usefixtures("use_clc")
@pytest.mark.parametrize("use_port", [5098])
@pytest.mark.parametrize("use_comm_type", [CommType.SERIAL])
class TestInterRequestDelay:
    """Exercise real transactions with mocked serial I/O."""

    @pytest_asyncio.fixture(
        name="transact", params=[False, True], ids=["async", "sync"]
    )
    async def transaction(self, request, use_clc):
        """Use the existing communication fixture for both transaction paths."""
        use_clc.inter_request_delay = 0.02
        use_clc.timeout_connect = 0.05
        client = mock.Mock() if request.param else None
        manager = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            0,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        manager.connection_made(mock.Mock())
        yield manager
        manager.close()

    @pytest.fixture(name="wire")
    def serial_output(self, transact):
        """Observe bytes sent without replacing transaction methods."""
        return (
            transact.sync_client.send if transact.is_sync else transact.transport.write
        )

    async def execute(self, transact, no_response=False, dev_id=1):
        """Send one request through the selected transaction implementation."""
        request = ReadCoilsRequest(address=0, count=1, dev_id=dev_id)
        if transact.is_sync:
            return transact.sync_execute(no_response, request)
        return await transact.execute(no_response, request)

    @pytest.mark.parametrize(
        ("delay", "last_end", "now", "expected"),
        [
            (0.0, 100.0, 100.0, 0.0),
            (0.02, None, 100.0, 0.0),
            (0.02, 100.0, 100.0, 0.02),
            (0.02, 100.0, 100.01, 0.01),
            (0.02, 100.0, 100.02, 0.0),
            (0.02, 100.0, 101.0, 0.0),
        ],
    )
    async def test_remaining_interval(self, transact, delay, last_end, now, expected):
        """First requests, disabled spacing and elapsed idle time need no wait."""
        transact.comm_params.inter_request_delay = delay
        transact._last_transaction_end = {} if last_end is None else {1: last_end}
        # Replace only the imported reference owned by the transaction module.
        with mock.patch.object(transaction_module, "monotonic", return_value=now):
            assert transact._inter_request_delay(1) == pytest.approx(expected)

    @pytest.mark.parametrize("delay", [0.0, 0.02])
    async def test_completion_spacing(self, transact, wire, delay):
        """Measure the interval from response completion, not request start."""
        transact.comm_params.inter_request_delay = delay
        starts, completions = [], []
        response = transact.framer.buildFrame(ReadCoilsResponse(dev_id=1, bits=[True]))

        def receive():
            completions.append(monotonic())
            transact.data_received(response)

        def send(*_args, **_kwargs):
            starts.append(monotonic())
            if not transact.is_sync:
                asyncio.get_running_loop().call_later(0.03, receive)

        def read(_size):
            sleep(0.03)
            completions.append(monotonic())
            return response

        wire.side_effect = send
        if transact.is_sync:
            transact.sync_client.recv.side_effect = read
        for _ in range(2):
            result = await self.execute(transact)
            assert result.bits[0]
        assert len(starts) == len(completions) == 2
        assert starts[1] - completions[0] >= delay - 0.001
        assert (not transact._last_transaction_end) == (delay == 0.0)

    async def test_timeouts_retries_and_next_call(self, transact, wire):
        """Real receive timeouts pace retries and the next transaction."""
        transact.retries = 1
        gaps = []

        def send(*_args, **_kwargs):
            if 1 in transact._last_transaction_end:
                gaps.append(monotonic() - transact._last_transaction_end[1])

        wire.side_effect = send
        if transact.is_sync:
            transact.sync_client.recv.return_value = b""
        for _ in range(2):
            with pytest.raises(ModbusIOException):
                await self.execute(transact)
        assert wire.call_count == 4
        minimum = transact.comm_params.inter_request_delay
        assert len(gaps) == 3
        assert all(gap >= minimum - 0.001 for gap in gaps)

    async def test_no_response_and_independent_clients(self, transact, wire, use_clc):
        """No-response transactions record completion only on their own client."""
        client = mock.Mock() if transact.is_sync else None
        second = TransactionManager(
            use_clc,
            FramerRTU(DecodePDU(False)),
            0,
            False,
            None,
            None,
            None,
            sync_client=client,
        )
        second.connection_made(mock.Mock())
        starts = []
        wire.side_effect = lambda *_args, **_kwargs: starts.append(monotonic())
        try:
            await self.execute(transact, True)
            assert 1 in transact._last_transaction_end
            previous_completion = second._last_transaction_end.get(1)
            assert previous_completion is None
            assert second._inter_request_delay(1) == 0.0
            await self.execute(second, True)
            assert 1 in second._last_transaction_end
            await self.execute(transact, True)
            assert starts[1] - starts[0] >= 0.019
        finally:
            second.close()

    @pytest.mark.parametrize("error", [OSError, asyncio.TimeoutError])
    async def test_send_error_propagates_and_paces_next_attempt(
        self, transact, wire, error
    ):
        """Send errors propagate without entering the receive retry handler."""
        transact.retries = 1
        wire.side_effect = error("send failed")
        with pytest.raises(error, match="send failed"):
            await self.execute(transact, True)
        assert wire.call_count == 1
        completed = transact._last_transaction_end.get(1)
        assert completed is not None
        starts = []
        wire.side_effect = lambda *_args, **_kwargs: starts.append(monotonic())
        await self.execute(transact, True)
        assert starts[0] - completed >= 0.019

    @pytest.mark.parametrize(
        "client_class", [ModbusSerialClient, AsyncModbusSerialClient]
    )
    @pytest.mark.parametrize("delay", [-1.0, math.nan, math.inf])
    async def test_invalid_serial_delay(self, client_class, delay):
        """Reject delay values that cannot define a finite nonnegative interval."""
        with pytest.raises(ValueError, match="inter_request_delay"):
            client_class("test", inter_request_delay=delay)

    @pytest.mark.parametrize(
        "client_class", [ModbusSerialClient, AsyncModbusSerialClient]
    )
    async def test_serial_option_forwarding(self, client_class):
        """Both public clients default to zero and forward explicit delays."""
        for kwargs, expected in (({}, 0.0), ({"inter_request_delay": 0.02}, 0.02)):
            client = client_class("test", **kwargs)
            try:
                transact = (
                    client.transaction
                    if isinstance(client, ModbusSerialClient)
                    else client.ctx
                )
                assert transact.comm_params.inter_request_delay == expected
            finally:
                client.close()

    @pytest.mark.parametrize("transact", [False], indirect=True)
    async def test_async_same_device_callers(self, transact, wire):
        """Queued requests to the same slave preserve the delay interval."""
        starts = []
        wire.side_effect = lambda *_args, **_kwargs: starts.append(monotonic())
        await self.execute(transact, True)
        await asyncio.wait_for(
            asyncio.gather(self.execute(transact, True), self.execute(transact, True)),
            timeout=2,
        )
        assert len(starts) == 3
        assert all(later - earlier >= 0.019 for earlier, later in pairwise(starts))

    @pytest.mark.parametrize("transact", [False], indirect=True)
    async def test_cancel_during_idle_interval(self, transact, wire):
        """Cancellation sends nothing and does not reset the last completion."""
        transact.comm_params.inter_request_delay = 0.1
        await self.execute(transact, True)
        completed = transact._last_transaction_end.get(1)
        waiting = asyncio.Event()
        original_delay = transact._inter_request_delay

        def observe_delay(dev_id):
            waiting.set()
            return original_delay(dev_id)

        with mock.patch.object(
            transact, "_inter_request_delay", side_effect=observe_delay
        ):
            pending = asyncio.create_task(self.execute(transact, True))
            try:
                await asyncio.wait_for(waiting.wait(), timeout=2)
                pending.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await pending
            finally:
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
        assert wire.call_count == 1
        assert transact._last_transaction_end.get(1) == completed
        starts = []
        wire.side_effect = lambda *_args, **_kwargs: starts.append(monotonic())
        await self.execute(transact, True)
        assert wire.call_count == 2
        assert starts[0] - completed >= 0.099

    async def test_device_intervals_and_broadcasts(self, transact):
        """Other devices retain independent deadlines; broadcasts affect all."""
        with mock.patch.object(transaction_module, "monotonic", return_value=100.0):
            transact._set_transaction_end(1)
            assert transact._inter_request_delay(1) == pytest.approx(0.02)
            assert transact._inter_request_delay(2) == 0.0
            assert transact._inter_request_delay(0) == pytest.approx(0.02)
        with mock.patch.object(transaction_module, "monotonic", return_value=100.01):
            transact._set_transaction_end(2)
            assert transact._inter_request_delay(1) == pytest.approx(0.01)
            assert transact._inter_request_delay(2) == pytest.approx(0.02)
            transact._set_transaction_end(0)
            assert transact._inter_request_delay(1) == pytest.approx(0.02)
            assert transact._inter_request_delay(3) == pytest.approx(0.02)

    async def test_interleaved_devices(self, transact, wire):
        """Requests to B do not reset A's delay interval."""
        starts = []
        wire.side_effect = lambda *_args, **_kwargs: starts.append(monotonic())
        await self.execute(transact, True, 1)
        completed = transact._last_transaction_end[1]
        await self.execute(transact, True, 2)
        assert transact._last_transaction_end[1] == completed
        await self.execute(transact, True, 1)
        assert starts[2] - completed >= 0.019

    @pytest.mark.parametrize("transact", [False], indirect=True)
    async def test_ready_device_overtakes_waiting_device(self, transact, wire):
        """Waiting for a delay interval must not reserve the wire against device B."""
        transact.comm_params.inter_request_delay = 0.2
        sent = []
        wire.side_effect = lambda data: sent.append(data[0])
        await self.execute(transact, True, 1)
        waiting = asyncio.Event()
        original_delay = transact._inter_request_delay

        def observe_delay(dev_id):
            waiting.set()
            return original_delay(dev_id)

        with mock.patch.object(
            transact, "_inter_request_delay", side_effect=observe_delay
        ):
            pending = asyncio.create_task(self.execute(transact, True, 1))
            try:
                await asyncio.wait_for(waiting.wait(), 2)
                await self.execute(transact, True, 2)
                assert sent == [1, 2]
                await asyncio.wait_for(pending, 2)
                assert sent == [1, 2, 1]
            finally:
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)

    @pytest.mark.parametrize("transact", [False], indirect=True)
    async def test_other_device_waits_for_active_response(self, transact, wire):
        """Delay intervals can overlap other work, but wire transactions cannot."""
        sent = []
        started = asyncio.Event()

        def send(data):
            sent.append(data[0])
            started.set()

        wire.side_effect = send
        transact.comm_params.timeout_connect = 2
        first = asyncio.create_task(self.execute(transact, False, 1))
        second = asyncio.create_task(self.execute(transact, True, 2))
        try:
            await asyncio.wait_for(started.wait(), 1)
            await asyncio.sleep(0)
            assert sent == [1]
            response = transact.framer.buildFrame(
                ReadCoilsResponse(dev_id=1, bits=[True])
            )
            transact.data_received(response)
            await asyncio.wait_for(asyncio.gather(first, second), 2)
            assert sent == [1, 2]
        finally:
            first.cancel()
            second.cancel()
            await asyncio.gather(first, second, return_exceptions=True)

    @pytest.mark.parametrize("transact", [False], indirect=True)
    async def test_cancel_while_waiting_for_wire_lock(self, transact, wire):
        """A cancelled waiter must not release another caller's wire lock."""
        await transact._lock.acquire()
        pending = asyncio.create_task(self.execute(transact, True))
        try:
            await asyncio.sleep(0)
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await pending
            assert transact._lock.locked()
            wire.assert_not_called()
            assert transact._last_transaction_end == {}
        finally:
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)
            transact._lock.release()
        await asyncio.wait_for(self.execute(transact, True), 1)
        wire.assert_called_once()
        assert not transact._lock.locked()

    @pytest.mark.parametrize("transact", [False], indirect=True)
    async def test_other_device_runs_during_retry_delay(self, transact, wire):
        """A timed-out slave's retry interval must not reserve the wire."""
        transact.retries = 1
        transact.comm_params.inter_request_delay = 0.2
        sent = []
        wire.side_effect = lambda data: sent.append(data[0])
        retry_waiting = asyncio.Event()
        original_delay = transact._inter_request_delay

        def observe_delay(dev_id):
            if dev_id == 1 and sent:
                retry_waiting.set()
            return original_delay(dev_id)

        with mock.patch.object(
            transact, "_inter_request_delay", side_effect=observe_delay
        ):
            pending = asyncio.create_task(self.execute(transact, False, 1))
            try:
                await asyncio.wait_for(retry_waiting.wait(), 2)
                await self.execute(transact, True, 2)
                assert sent == [1, 2]
                with pytest.raises(ModbusIOException):
                    await asyncio.wait_for(pending, 2)
                assert sent == [1, 2, 1]
                assert not transact._lock.locked()
            finally:
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
