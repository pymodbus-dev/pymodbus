#!/usr/bin/env python3
"""Pymodbus Client modbus all calls example.

Please see method **template_call**
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
import logging

import client_sync

import pymodbus.diag_message as req_diag
import pymodbus.mei_message as req_mei
import pymodbus.other_message as req_other
from pymodbus.exceptions import ModbusException


_logger = logging.getLogger(__file__)
_logger.setLevel("DEBUG")


SLAVE = 0x01


# --------------------------------------------------
# Template on how to make modbus calls (sync/async).
# all calls follow the same schema,
# --------------------------------------------------
def template_call(client):
    """Show complete modbus call, sync version."""
    try:
        rr = client.read_coils(32, 1, slave=SLAVE)
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
def handle_coils(client):
    """Read/Write coils."""
    _logger.info("### Reading Coil different number of bits (return 8 bits multiples)")
    rr = client.read_coils(1, 1, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 8

    rr = client.read_coils(1, 5, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 8

    rr = client.read_coils(1, 12, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 16

    rr = client.read_coils(1, 17, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 24

    _logger.info("### Write false/true to coils and read to verify")
    client.write_coil(0, True, slave=SLAVE)
    rr = client.read_coils(0, 1, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.bits[0]  # test the expected value

    client.write_coils(1, [True] * 21, slave=SLAVE)
    rr = client.read_coils(1, 21, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    resp = [True] * 21
    # If the returned output quantity is not a multiple of eight,
    # the remaining bits in the final data byte will be padded with zeros
    # (toward the high order end of the byte).
    resp.extend([False] * 3)
    assert rr.bits == resp  # test the expected value

    _logger.info("### Write False to address 1-8 coils")
    client.write_coils(1, [False] * 8, slave=SLAVE)
    rr = client.read_coils(1, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.bits == [False] * 8  # test the expected value


def handle_discrete_input(client):
    """Read discrete inputs."""
    _logger.info("### Reading discrete input, Read address:0-7")
    rr = client.read_discrete_inputs(0, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.bits) == 8


def handle_holding_registers(client):
    """Read/write holding registers."""
    _logger.info("### write holding register and read holding registers")
    client.write_register(1, 10, slave=SLAVE)
    rr = client.read_holding_registers(1, 1, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.registers[0] == 10

    client.write_registers(1, [10] * 8, slave=SLAVE)
    rr = client.read_holding_registers(1, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.registers == [10] * 8

    _logger.info("### write read holding registers, using **kwargs")
    arguments = {
        "read_address": 1,
        "read_count": 8,
        "write_address": 1,
        "values": [256, 128, 100, 50, 25, 10, 5, 1],
    }
    client.readwrite_registers(slave=SLAVE, **arguments)
    rr = client.read_holding_registers(1, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert rr.registers == arguments["values"]


def handle_input_registers(client):
    """Read input registers."""
    _logger.info("### read input registers")
    rr = client.read_input_registers(1, 8, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    assert len(rr.registers) == 8


def execute_information_requests(client):  # pragma no cover
    """Execute extended information requests."""
    _logger.info("### Running information requests.")
    rr = client.execute(req_mei.ReadDeviceInformationRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    assert rr.information[0] == b"Pymodbus"

    rr = client.execute(req_other.ReportSlaveIdRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    # assert rr.status

    rr = client.execute(req_other.ReadExceptionStatusRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    # assert not rr.status

    rr = client.execute(req_other.GetCommEventCounterRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    # assert rr.status
    # assert not rr.count

    rr = client.execute(req_other.GetCommEventLogRequest(slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    # assert rr.status
    # assert not (rr.event_count + rr.message_count + len(rr.events))


def execute_diagnostic_requests(client):  # pragma no cover
    """Execute extended diagnostic requests."""
    _logger.info("### Running diagnostic requests.")
    message = b"OK"
    rr = client.execute(req_diag.ReturnQueryDataRequest(message=message, slave=SLAVE))
    assert not rr.isError()  # test that call was OK
    assert rr.message == message

    client.execute(req_diag.RestartCommunicationsOptionRequest(slave=SLAVE))
    client.execute(req_diag.ReturnDiagnosticRegisterRequest(slave=SLAVE))
    client.execute(req_diag.ChangeAsciiInputDelimiterRequest(slave=SLAVE))

    # NOT WORKING: _check_call(client.execute(req_diag.ForceListenOnlyModeRequest(slave=SLAVE)))
    # does not send a response

    client.execute(req_diag.ClearCountersRequest())
    client.execute(req_diag.ReturnBusCommunicationErrorCountRequest(slave=SLAVE))
    client.execute(req_diag.ReturnBusExceptionErrorCountRequest(slave=SLAVE))
    client.execute(req_diag.ReturnSlaveMessageCountRequest(slave=SLAVE))
    client.execute(req_diag.ReturnSlaveNoResponseCountRequest(slave=SLAVE))
    client.execute(req_diag.ReturnSlaveNAKCountRequest(slave=SLAVE))
    client.execute(req_diag.ReturnSlaveBusyCountRequest(slave=SLAVE))
    client.execute(req_diag.ReturnSlaveBusCharacterOverrunCountRequest(slave=SLAVE))
    client.execute(req_diag.ReturnIopOverrunCountRequest(slave=SLAVE))
    client.execute(req_diag.ClearOverrunCountRequest(slave=SLAVE))
    # NOT WORKING _check_call(client.execute(req_diag.GetClearModbusPlusRequest(slave=SLAVE)))


# ------------------------
# Run the calls in groups.
# ------------------------
def run_sync_calls(client):
    """Demonstrate basic read/write calls."""
    template_call(client)
    handle_coils(client)
    handle_discrete_input(client)
    handle_holding_registers(client)
    handle_input_registers(client)
    # awaiting fix: execute_information_requests(client)
    # awaiting fix: execute_diagnostic_requests(client)


def main(cmdline=None):
    """Combine setup and run."""
    client = client_sync.setup_sync_client(
        description="Run synchronous client.", cmdline=cmdline
    )
    client_sync.run_sync_client(client, modbus_calls=run_sync_calls)


if __name__ == "__main__":
    main()  # pragma: no cover
