#!/usr/bin/env python3
"""Pymodbus Client modbus async all calls example.

Please see method **async_template_call**
for a template on how to make modbus calls and check for different
error conditions.

The handle* functions each handle a set of modbus calls with the
same register type (e.g. coils).

All available modbus calls are present.

If you are performing a request that is not available in the client
mixin, you have to perform the request like this instead::

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

import client_async

import pymodbus.diag_message as req_diag
import pymodbus.mei_message as req_mei
import pymodbus.other_message as req_other
from pymodbus.exceptions import ModbusException


logging.basicConfig()
_logger = logging.getLogger(__file__)
_logger.setLevel("DEBUG")


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

    # Validate data
    txt = f"### Template coils response: {rr.bits!s}"
    _logger.debug(txt)


# ------------------------------------------------------
# Call modbus device (all possible calls are presented).
# ------------------------------------------------------
async def async_handle_coils(client):
    """Read/Write coils."""
    _logger.info("### Reading Coil different number of bits (return 8 bits multiples)")
    rr = await client.read_coils(1, 1, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 8

    rr = await client.read_coils(1, 5, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 8

    rr = await client.read_coils(1, 12, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 16

    rr = await client.read_coils(1, 17, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 24

    _logger.info("### Write false/true to coils and read to verify")
    await client.write_coil(0, True, slave=SLAVE)
    rr = await client.read_coils(0, 1, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.bits[0]  # test the expected value

    await client.write_coils(1, [True] * 21, slave=SLAVE)
    rr = await client.read_coils(1, 21, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    resp = [True] * 21
    # If the returned output quantity is not a multiple of eight,
    # the remaining bits in the final data byte will be padded with zeros
    # (toward the high order end of the byte).
    resp.extend([False] * 3)
    assert rr.bits == resp  # test the expected value

    _logger.info("### Write False to address 1-8 coils")
    await client.write_coils(1, [False] * 8, slave=SLAVE)
    rr = await client.read_coils(1, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.bits == [False] * 8  # test the expected value


async def async_handle_discrete_input(client):
    """Read discrete inputs."""
    _logger.info("### Reading discrete input, Read address:0-7")
    rr = await client.read_discrete_inputs(0, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 8


async def async_handle_holding_registers(client):
    """Read/write holding registers."""
    _logger.info("### write holding register and read holding registers")
    await client.write_register(1, 10, slave=SLAVE)
    rr = await client.read_holding_registers(1, 1, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.registers[0] == 10

    await client.write_registers(1, [10] * 8, slave=SLAVE)
    rr = await client.read_holding_registers(1, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.registers == [10] * 8

    _logger.info("### write read holding registers, using **kwargs")
    arguments = {
        "read_address": 1,
        "read_count": 8,
        "write_address": 1,
        "values": [256, 128, 100, 50, 25, 10, 5, 1],
    }
    await client.readwrite_registers(slave=SLAVE, **arguments)
    rr = await client.read_holding_registers(1, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.registers == arguments["values"]


async def async_handle_input_registers(client):
    """Read input registers."""
    _logger.info("### read input registers")
    rr = await client.read_input_registers(1, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.registers) == 8


async def async_execute_information_requests(client):
    """Execute extended information requests."""
    _logger.info("### Running information requests.")
    rr = await client.execute(req_mei.ReadDeviceInformationRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    assert rr.information[0] == b"Pymodbus"

    rr = await client.execute(req_other.ReportSlaveIdRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    # assert rr.status

    rr = await client.execute(req_other.ReadExceptionStatusRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    # assert not rr.status

    rr = await client.execute(req_other.GetCommEventCounterRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    # assert rr.status
    # assert not rr.count

    rr = await client.execute(req_other.GetCommEventLogRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    # assert rr.status
    # assert not (rr.event_count + rr.message_count + len(rr.events))


async def async_execute_diagnostic_requests(client):
    """Execute extended diagnostic requests."""
    _logger.info("### Running diagnostic requests.")
    message = b"OK"
    rr = await client.execute(
        req_diag.ReturnQueryDataRequest(message=message, slave=SLAVE)
    )
    assert not rr.isError()  # test that call was OK
    assert rr.message == message

    await client.execute(req_diag.RestartCommunicationsOptionRequest(slave=SLAVE))
    await client.execute(req_diag.ReturnDiagnosticRegisterRequest(slave=SLAVE))
    await client.execute(req_diag.ChangeAsciiInputDelimiterRequest(slave=SLAVE))

    # NOT WORKING: _check_call(await client.execute(req_diag.ForceListenOnlyModeRequest(slave=SLAVE)))
    # does not send a response

    await client.execute(req_diag.ClearCountersRequest())
    await client.execute(req_diag.ReturnBusCommunicationErrorCountRequest(slave=SLAVE))
    await client.execute(req_diag.ReturnBusExceptionErrorCountRequest(slave=SLAVE))
    await client.execute(req_diag.ReturnSlaveMessageCountRequest(slave=SLAVE))
    await client.execute(req_diag.ReturnSlaveNoResponseCountRequest(slave=SLAVE))
    await client.execute(req_diag.ReturnSlaveNAKCountRequest(slave=SLAVE))
    await client.execute(req_diag.ReturnSlaveBusyCountRequest(slave=SLAVE))
    await client.execute(
        req_diag.ReturnSlaveBusCharacterOverrunCountRequest(slave=SLAVE)
    )
    await client.execute(req_diag.ReturnIopOverrunCountRequest(slave=SLAVE))
    await client.execute(req_diag.ClearOverrunCountRequest(slave=SLAVE))
    # NOT WORKING _check_call(await client.execute(req_diag.GetClearModbusPlusRequest(slave=SLAVE)))


# ------------------------
# Run the calls in groups.
# ------------------------
async def run_async_calls(client):
    """Demonstrate basic read/write calls."""
    await async_template_call(client)
    await async_handle_coils(client)
    await async_handle_discrete_input(client)
    await async_handle_holding_registers(client)
    await async_handle_input_registers(client)
    await async_execute_information_requests(client)
    await async_execute_diagnostic_requests(client)


async def main(cmdline=None):
    """Combine setup and run."""
    testclient = client_async.setup_async_client(
        description="Run asynchronous client.", cmdline=cmdline
    )
    await client_async.run_async_client(testclient, modbus_calls=run_async_calls)


if __name__ == "__main__":
    asyncio.run(main())  # pragma: no cover
