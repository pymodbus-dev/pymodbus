#!/usr/bin/env python3
"""Pymodbus Synchronous Client extended calls rxample.

This example uses client_sync.py to handle connection, and have the same options.

The example shows how to use the synchronous modbus client
implementation from pymodbus to perform the extended portions of the
modbus protocol.

If you are performing a request that is not available in the client
mixin, you have to perform the request like this instead:

from pymodbus.diag_message import ClearCountersRequest
from pymodbus.diag_message import ClearCountersResponse

request  = ClearCountersRequest()
response = client.execute(request)
if isinstance(response, ClearCountersResponse):
    ... do something with the response


The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""
import asyncio

from examples.client_async import _logger, run_client, setup_client

from pymodbus.diag_message import (
    ChangeAsciiInputDelimiterRequest,
    ClearCountersRequest,
    ClearOverrunCountRequest,
    ForceListenOnlyModeRequest,
    GetClearModbusPlusRequest,
    RestartCommunicationsOptionRequest,
    ReturnBusCommunicationErrorCountRequest,
    ReturnBusExceptionErrorCountRequest,
    ReturnDiagnosticRegisterRequest,
    ReturnIopOverrunCountRequest,
    ReturnQueryDataRequest,
    ReturnSlaveBusCharacterOverrunCountRequest,
    ReturnSlaveBusyCountRequest,
    ReturnSlaveMessageCountRequest,
    ReturnSlaveNAKCountRequest,
    ReturnSlaveNoResponseCountRequest,
)
from pymodbus.mei_message import ReadDeviceInformationRequest
from pymodbus.other_message import (
    GetCommEventCounterRequest,
    GetCommEventLogRequest,
    ReadExceptionStatusRequest,
    ReportSlaveIdRequest,
)

UNIT = 0x01


async def execute_information_requests(client):
    """Execute extended information requests."""
    _logger.info("### Running ReadDeviceInformationRequest")
    rr = await client.execute(ReadDeviceInformationRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReportSlaveIdRequest")
    rr = await client.execute(ReportSlaveIdRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert rr.status  # test that the status is ok

    _logger.info("Running ReadExceptionStatusRequest")
    rr = await client.execute(ReadExceptionStatusRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert not rr.status  # test the status code

    _logger.info("Running GetCommEventCounterRequest")
    rr = await client.execute(GetCommEventCounterRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert rr.status  # test the status code
    assert not rr.count  # test the count returned

    _logger.info("Running GetCommEventLogRequest")
    rr = await client.execute(GetCommEventLogRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert rr.status  # test the status code
    assert not rr.event_count  # test the number of events
    assert not rr.message_count  # test the number of messages
    assert not rr.events  # test the number of events


async def execute_diagnostic_requests(client):
    """Execute extended diagnostic requests."""
    _logger.info("### Running ReturnQueryDataRequest")
    rr = await client.execute(ReturnQueryDataRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert not rr.message[0]  # test the resulting message

    _logger.info("Running RestartCommunicationsOptionRequest")
    rr = await client.execute(RestartCommunicationsOptionRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert not rr.message[0]  # test the resulting message

    _logger.info("Running ReturnDiagnosticRegisterRequest")
    rr = await client.execute(ReturnDiagnosticRegisterRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ChangeAsciiInputDelimiterRequest")
    rr = await client.execute(ChangeAsciiInputDelimiterRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ForceListenOnlyModeRequest")
    _logger.info("NOT WORKING")
    _logger.info(str(ForceListenOnlyModeRequest))
    # rr = await client.execute(
    #     ForceListenOnlyModeRequest(unit=UNIT)
    # )  # does not send a response
    # assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ClearCountersRequest")
    rr = await client.execute(ClearCountersRequest())
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnBusCommunicationErrorCountRequest")
    rr = await client.execute(ReturnBusCommunicationErrorCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnBusExceptionErrorCountRequest")
    rr = await client.execute(ReturnBusExceptionErrorCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveMessageCountRequest")
    rr = await client.execute(ReturnSlaveMessageCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveNoResponseCountRequest")
    rr = await client.execute(ReturnSlaveNoResponseCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveNAKCountRequest")
    rr = await client.execute(ReturnSlaveNAKCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveBusyCountRequest")
    rr = await client.execute(ReturnSlaveBusyCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveBusCharacterOverrunCountRequest")
    rr = await client.execute(ReturnSlaveBusCharacterOverrunCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnIopOverrunCountRequest")
    rr = await client.execute(ReturnIopOverrunCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ClearOverrunCountRequest")
    rr = await client.execute(ClearOverrunCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running GetClearModbusPlusRequest")
    rr = await client.execute(GetClearModbusPlusRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK


async def demonstrate_calls(client):
    """Demonstrate basic read/write calls."""
    await execute_information_requests(client)
    await execute_diagnostic_requests(client)


if __name__ == "__main__":
    testclient = setup_client()
    asyncio.run(run_client(testclient, modbus_calls=demonstrate_calls))
