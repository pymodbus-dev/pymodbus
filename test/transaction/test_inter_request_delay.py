"""Test optional serial transaction spacing without wall-clock delays."""

import asyncio
import math
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import mock

import pytest

import pymodbus.transaction.transaction as transaction_module
from pymodbus.client import AsyncModbusSerialClient, ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.framer import FramerRTU
from pymodbus.pdu import DecodePDU
from pymodbus.pdu.bit_message import ReadCoilsRequest, ReadCoilsResponse
from pymodbus.transaction import TransactionManager
from pymodbus.transport import CommParams, CommType


@pytest.fixture(name="clock")
def fake_clock(monkeypatch):
    """Provide monotonic time and advancing sync/async sleeps."""
    now, waits = [100.0], []

    def sleep(delay):
        waits.append(delay)
        now[0] += delay

    async def async_sleep(delay):
        sleep(delay)

    monkeypatch.setattr(transaction_module, "monotonic", lambda: now[0])
    monkeypatch.setattr(transaction_module, "sleep", sleep)
    monkeypatch.setattr(transaction_module.asyncio, "sleep", async_sleep)
    return now, waits


def manager(sync, delay, retries=0):
    """Construct a transaction manager without opening a port."""
    params = CommParams(
        comm_type=CommType.SERIAL, inter_request_delay=delay, timeout_connect=1
    )
    client = mock.Mock() if sync else None
    result = TransactionManager(
        params,
        FramerRTU(DecodePDU(False)),
        retries,
        False,
        None,
        None,
        None,
        sync_client=client,
    )
    result.transport = mock.Mock()
    return result


async def execute(transact, sync, no_response=False):
    """Run the same request through either implementation."""
    request = ReadCoilsRequest(address=0, count=1, dev_id=1)
    if sync:
        return transact.sync_execute(no_response, request)
    return await transact.execute(no_response, request)


@pytest.mark.parametrize("sync", [False, True])
@pytest.mark.parametrize("delay", [0.0, 0.02])
async def test_completion_spacing_and_idle_time(clock, monkeypatch, sync, delay):
    """Count from response completion, skip the first wait and credit idle time."""
    now, waits = clock
    transact = manager(sync, delay)
    starts = []

    def send(request):
        starts.append(now[0])
        response = ReadCoilsResponse(dev_id=1, transaction_id=request.transaction_id)

        def receive(*_args):
            now[0] += 0.03
            if not sync:
                transact.response_future.set_result(response)
            return response

        if sync:
            monkeypatch.setattr(transact, "sync_get_response", receive)
        else:
            asyncio.get_running_loop().call_soon(receive)

    monkeypatch.setattr(transact, "pdu_send", send)
    for _ in range(2):
        await execute(transact, sync)
    assert starts == pytest.approx([100.0, 100.03 + delay])
    now[0] += 1
    await execute(transact, sync)
    assert len(waits) == (1 if delay else 0)


@pytest.mark.parametrize("sync", [False, True])
async def test_timeouts_retries_and_next_call(clock, monkeypatch, sync):
    """Timeouts pace retries and subsequent calls, preserving the original error."""
    now, waits = clock
    transact = manager(sync, 0.02, retries=1)
    send = mock.Mock()
    monkeypatch.setattr(transact, "pdu_send", send)

    def timeout(*_args, **_kwargs):
        now[0] += 0.2
        raise asyncio.TimeoutError

    async def async_timeout(*args, **kwargs):
        return timeout(*args, **kwargs)

    monkeypatch.setattr(transact, "sync_get_response", timeout)
    monkeypatch.setattr(transaction_module.asyncio, "wait_for", async_timeout)
    for _ in range(2):
        with pytest.raises(ModbusIOException):
            await execute(transact, sync)
    assert send.call_count == 4
    assert waits == pytest.approx([0.02] * 3)


@pytest.mark.parametrize("sync", [False, True])
async def test_no_response_and_independent_clients(clock, monkeypatch, sync):
    """No-response sends are paced without sharing deadlines between clients."""
    _, waits = clock
    first, second = manager(sync, 0.02), manager(sync, 0.02)
    monkeypatch.setattr(first, "pdu_send", mock.Mock())
    monkeypatch.setattr(second, "pdu_send", mock.Mock())
    await execute(first, sync, True)
    await execute(second, sync, True)
    assert waits == []
    await execute(first, sync, True)
    assert waits == pytest.approx([0.02])


@pytest.mark.parametrize("sync", [False, True])
async def test_send_error_still_paces_next_attempt(clock, monkeypatch, sync):
    """An exceptional send must not bypass pacing."""
    _, waits = clock
    transact = manager(sync, 0.02)
    monkeypatch.setattr(
        transact, "pdu_send", mock.Mock(side_effect=[OSError("send failed"), None])
    )
    with pytest.raises(OSError, match="send failed"):
        await execute(transact, sync, True)
    await execute(transact, sync, True)
    assert waits == pytest.approx([0.02])


@pytest.mark.parametrize("client_class", [ModbusSerialClient, AsyncModbusSerialClient])
@pytest.mark.parametrize("delay", [-1, math.nan, math.inf])
async def test_invalid_serial_delay(client_class, delay):
    """Reject delay values that cannot define a finite nonnegative interval."""
    with pytest.raises(ValueError, match="inter_request_delay"):
        client_class("test", inter_request_delay=delay)


@pytest.mark.parametrize("client_class", [ModbusSerialClient, AsyncModbusSerialClient])
async def test_serial_option_forwarding(client_class):
    """Both public clients default to zero and forward explicit delays."""
    for kwargs, expected in (({}, 0.0), ({"inter_request_delay": 0.02}, 0.02)):
        client = client_class("test", **kwargs)
        transact = (
            client.transaction if isinstance(client, ModbusSerialClient) else client.ctx
        )
        assert transact.comm_params.inter_request_delay == expected
        client.close()


async def test_async_concurrent_callers(clock, monkeypatch):
    """Queued callers cannot send during another caller's idle interval."""
    now, waits = clock
    transact = manager(False, 0.02)
    starts = []
    sleeping, release = asyncio.Event(), asyncio.Event()

    async def sleep(delay):
        sleeping.set()
        await release.wait()
        waits.append(delay)
        now[0] += delay

    monkeypatch.setattr(transaction_module.asyncio, "sleep", sleep)
    monkeypatch.setattr(transact, "pdu_send", lambda _request: starts.append(now[0]))
    await execute(transact, False, True)
    second = asyncio.create_task(execute(transact, False, True))
    await asyncio.wait_for(sleeping.wait(), 1)
    third = asyncio.create_task(execute(transact, False, True))
    queued = asyncio.Event()
    asyncio.get_running_loop().call_soon(queued.set)
    await queued.wait()
    assert starts == [100.0]
    release.set()
    await asyncio.wait_for(asyncio.gather(second, third), 1)
    assert starts == pytest.approx([100.0, 100.02, 100.04])
    assert waits == pytest.approx([0.02, 0.02])


async def test_sync_concurrent_callers(clock, monkeypatch):
    """Threads sharing a client retain spacing while queued on its lock."""
    now, waits = clock
    transact = manager(True, 0.02)
    starts = []
    sleeping, release = Event(), Event()

    def sleep(delay):
        sleeping.set()
        assert release.wait(2)
        waits.append(delay)
        now[0] += delay

    monkeypatch.setattr(transaction_module, "sleep", sleep)
    monkeypatch.setattr(transact, "pdu_send", lambda _request: starts.append(now[0]))
    await execute(transact, True, True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        second = executor.submit(transact.sync_execute, True, ReadCoilsRequest())
        try:
            assert sleeping.wait(2)
            third = executor.submit(transact.sync_execute, True, ReadCoilsRequest())
            assert starts == [100.0]
        finally:
            release.set()
        second.result(timeout=2)
        third.result(timeout=2)
    assert starts == pytest.approx([100.0, 100.02, 100.04])
    assert waits == pytest.approx([0.02, 0.02])


async def test_cancel_during_idle_interval(clock, monkeypatch):
    """Cancellation sends nothing and preserves the remaining idle interval."""
    now, waits = clock
    transact = manager(False, 0.02)
    send = mock.Mock()
    monkeypatch.setattr(transact, "pdu_send", send)
    await execute(transact, False, True)
    sleeping = asyncio.Event()

    async def sleep(_delay):
        sleeping.set()
        await asyncio.Future()

    monkeypatch.setattr(transaction_module.asyncio, "sleep", sleep)
    pending = asyncio.create_task(execute(transact, False, True))
    await asyncio.wait_for(sleeping.wait(), 1)
    now[0] += 0.01
    pending.cancel()
    with pytest.raises(asyncio.CancelledError):
        await pending
    assert send.call_count == 1

    async def finish_sleep(delay):
        waits.append(delay)
        now[0] += delay

    monkeypatch.setattr(transaction_module.asyncio, "sleep", finish_sleep)
    await execute(transact, False, True)
    assert send.call_count == 2
    assert waits == pytest.approx([0.01])
