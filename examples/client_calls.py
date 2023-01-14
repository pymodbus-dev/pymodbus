#!/usr/bin/env python3
"""Pymodbus Client modbus call examples.

Please see:

    async_template_call

    template_call

for a template on how to make modbus calls and check for different
error conditions.

The _handle_.... functions each handle a set of modbus calls with the
same register type (e.g. coils).

All available modbus calls are present. The difference between async
and sync is a single 'await' so the calls are not repeated.

If you are performing a request that is not available in the client
mixin, you have to perform the request like this instead:

from pymodbus.diag_message import ClearCountersRequest
from pymodbus.diag_message import ClearCountersResponse

request  = ClearCountersRequest()
response = client.execute(request)
if isinstance(response, ClearCountersResponse):
    ... do something with the response

This example uses client_async.py and client_sync.py to handle connection,
and have the same options.

The corresponding server must be started before e.g. as:

    ./server_async.py
"""
import asyncio
import logging

import pymodbus.diag_message as req_diag
import pymodbus.mei_message as req_mei
import pymodbus.other_message as req_other
from examples.client_async import run_async_client, setup_async_client
from examples.client_sync import run_sync_client, setup_sync_client
from examples.helper import get_commandline
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse


_logger = logging.getLogger()


SLAVE = 0x01


# --------------------------------------------------
# Template on how to make modbus calls (sync/async).
# all calls follow the same schema,
# --------------------------------------------------


async def async_template_call(client):
    """Show complete modbus call, async version."""
    try:
        rr = await client.read_coils(1, 1, slave=SLAVE)
    except ModbusException as exc:
        txt = f"ERROR: exception in pymodbus {exc}"
        _logger.error(txt)
        raise exc
    if rr.isError():
        txt = "ERROR: pymodbus returned an error!"
        _logger.error(txt)
        raise ModbusException(txt)
    if isinstance(rr, ExceptionResponse):
        txt = "ERROR: received exception from device {rr}!"
        _logger.error(txt)
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        raise ModbusException(txt)

    # Validate data
    txt = f"### Template coils response: {str(rr.bits)}"
    _logger.debug(txt)


def template_call(client):
    """Show complete modbus call, sync version."""
    try:
        rr = client.read_coils(1, 1, slave=SLAVE)
    except ModbusException as exc:
        txt = f"ERROR: exception in pymodbus {exc}"
        _logger.error(txt)
        raise exc
    if rr.isError():
        txt = "ERROR: pymodbus returned an error!"
        _logger.error(txt)
        raise ModbusException(txt)
    if isinstance(rr, ExceptionResponse):
        txt = "ERROR: received exception from device {rr}!"
        _logger.error(txt)
        # THIS IS NOT A PYTHON EXCEPTION, but a valid modbus message
        raise ModbusException(txt)

    # Validate data
    txt = f"### Template coils response: {str(rr.bits)}"
    _logger.debug(txt)


# -------------------------------------------------
# Generic error handling, to avoid duplicating code
# -------------------------------------------------


def _check_call(rr):
    """Check modbus call worked generically."""
    assert not rr.isError()  # test that call was OK
    assert not isinstance(rr, ExceptionResponse)  # Device rejected request
    return rr


# ------------------------------------------------------
# Call modbus device (all possible calls are presented).
# ------------------------------------------------------
async def _handle_coils(client):
    """Read/Write coils."""
    _logger.info("### Reading Coil different number of bits (return 8 bits multiples)")
    rr = _check_call(await client.read_coils(1, 1, slave=SLAVE))
    assert len(rr.bits) == 8

    rr = _check_call(await client.read_coils(1, 5, slave=SLAVE))
    assert len(rr.bits) == 8

    rr = _check_call(await client.read_coils(1, 12, slave=SLAVE))
    assert len(rr.bits) == 16

    rr = _check_call(await client.read_coils(1, 17, slave=SLAVE))
    assert len(rr.bits) == 24

    _logger.info("### Write false/true to coils and read to verify")
    _check_call(await client.write_coil(0, True, slave=SLAVE))
    rr = _check_call(await client.read_coils(0, 1, slave=SLAVE))
    assert rr.bits[0]  # test the expected value

    _check_call(await client.write_coils(1, [True] * 21, slave=SLAVE))
    rr = _check_call(await client.read_coils(1, 21, slave=SLAVE))
    resp = [True] * 21
    # If the returned output quantity is not a multiple of eight,
    # the remaining bits in the final data byte will be padded with zeros
    # (toward the high order end of the byte).
    resp.extend([False] * 3)
    assert rr.bits == resp  # test the expected value

    _logger.info("### Write False to address 1-8 coils")
    _check_call(await client.write_coils(1, [False] * 8, slave=SLAVE))
    rr = _check_call(await client.read_coils(1, 8, slave=SLAVE))
    assert rr.bits == [False] * 8  # test the expected value


async def _handle_discrete_input(client):
    """Read discrete inputs."""
    _logger.info("### Reading discrete input, Read address:0-7")
    rr = _check_call(await client.read_discrete_inputs(0, 8, slave=SLAVE))
    assert len(rr.bits) == 8


async def _handle_holding_registers(client):
    """Read/write holding registers."""
    _logger.info("### write holding register and read holding registers")
    _check_call(await client.write_register(1, 10, slave=SLAVE))
    rr = _check_call(await client.read_holding_registers(1, 1, slave=SLAVE))
    assert rr.registers[0] == 10

    _check_call(await client.write_registers(1, [10] * 8, slave=SLAVE))
    rr = _check_call(await client.read_holding_registers(1, 8, slave=SLAVE))
    assert rr.registers == [10] * 8

    _logger.info("### write read holding registers, using **kwargs")
    arguments = {
        "read_address": 1,
        "read_count": 8,
        "write_address": 1,
        "write_registers": [256, 128, 100, 50, 25, 10, 5, 1],
    }
    _check_call(await client.readwrite_registers(slave=SLAVE, **arguments))
    rr = _check_call(await client.read_holding_registers(1, 8, slave=SLAVE))
    assert rr.registers == arguments["write_registers"]


async def _handle_input_registers(client):
    """Read input registers."""
    _logger.info("### read input registers")
    rr = _check_call(await client.read_input_registers(1, 8, slave=SLAVE))
    assert len(rr.registers) == 8


async def _execute_information_requests(client):
    """Execute extended information requests."""
    _logger.info("### Running information requests.")
    rr = _check_call(
        await client.execute(req_mei.ReadDeviceInformationRequest(unit=SLAVE))
    )
    assert rr.information[0] == b"Pymodbus"

    rr = _check_call(await client.execute(req_other.ReportSlaveIdRequest(unit=SLAVE)))
    assert rr.status

    rr = _check_call(
        await client.execute(req_other.ReadExceptionStatusRequest(unit=SLAVE))
    )
    assert not rr.status

    rr = _check_call(
        await client.execute(req_other.GetCommEventCounterRequest(unit=SLAVE))
    )
    assert rr.status and not rr.count

    rr = _check_call(await client.execute(req_other.GetCommEventLogRequest(unit=SLAVE)))
    assert rr.status and not (rr.event_count + rr.message_count + len(rr.events))


async def _execute_diagnostic_requests(client):
    """Execute extended diagnostic requests."""
    _logger.info("### Running diagnostic requests.")
    rr = _check_call(await client.execute(req_diag.ReturnQueryDataRequest(unit=SLAVE)))
    assert not rr.message[0]

    _check_call(
        await client.execute(req_diag.RestartCommunicationsOptionRequest(unit=SLAVE))
    )
    _check_call(
        await client.execute(req_diag.ReturnDiagnosticRegisterRequest(unit=SLAVE))
    )
    _check_call(
        await client.execute(req_diag.ChangeAsciiInputDelimiterRequest(unit=SLAVE))
    )

    # NOT WORKING: _check_call(await client.execute(req_diag.ForceListenOnlyModeRequest(unit=SLAVE)))
    # does not send a response

    _check_call(await client.execute(req_diag.ClearCountersRequest()))
    _check_call(
        await client.execute(
            req_diag.ReturnBusCommunicationErrorCountRequest(unit=SLAVE)
        )
    )
    _check_call(
        await client.execute(req_diag.ReturnBusExceptionErrorCountRequest(unit=SLAVE))
    )
    _check_call(
        await client.execute(req_diag.ReturnSlaveMessageCountRequest(unit=SLAVE))
    )
    _check_call(
        await client.execute(req_diag.ReturnSlaveNoResponseCountRequest(unit=SLAVE))
    )
    _check_call(await client.execute(req_diag.ReturnSlaveNAKCountRequest(unit=SLAVE)))
    _check_call(await client.execute(req_diag.ReturnSlaveBusyCountRequest(unit=SLAVE)))
    _check_call(
        await client.execute(
            req_diag.ReturnSlaveBusCharacterOverrunCountRequest(unit=SLAVE)
        )
    )
    _check_call(await client.execute(req_diag.ReturnIopOverrunCountRequest(unit=SLAVE)))
    _check_call(await client.execute(req_diag.ClearOverrunCountRequest(unit=SLAVE)))
    # NOT WORKING _check_call(await client.execute(req_diag.GetClearModbusPlusRequest(unit=SLAVE)))


# ------------------------
# Run the calls in groups.
# ------------------------


async def run_async_calls(client):
    """Demonstrate basic read/write calls."""
    await async_template_call(client)
    await _handle_coils(client)
    await _handle_discrete_input(client)
    await _handle_holding_registers(client)
    await _handle_input_registers(client)
    await _execute_information_requests(client)
    await _execute_diagnostic_requests(client)


def run_sync_calls(client):
    """Demonstrate basic read/write calls."""
    template_call(client)


if __name__ == "__main__":
    cmd_args = get_commandline(
        server=False,
        description="Run modbus calls in asynchronous client.",
    )
    testclient = setup_async_client(cmd_args)
    asyncio.run(run_async_client(testclient, modbus_calls=run_async_calls))
    testclient = setup_sync_client(cmd_args)
    run_sync_client(testclient, modbus_calls=run_sync_calls)
