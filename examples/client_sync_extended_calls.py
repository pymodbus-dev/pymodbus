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
from examples.client_sync import _logger, run_client, setup_client

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


def execute_information_requests(client):
    """Execute extended information requests."""
    _logger.info("### Running ReadDeviceInformationRequest")
    rr = client.execute(ReadDeviceInformationRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReportSlaveIdRequest")
    rr = client.execute(ReportSlaveIdRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert rr.status  # test that the status is ok

    _logger.info("Running ReadExceptionStatusRequest")
    rr = client.execute(ReadExceptionStatusRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert not rr.status  # test the status code

    _logger.info("Running GetCommEventCounterRequest")
    rr = client.execute(GetCommEventCounterRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert rr.status  # test the status code
    assert not rr.count  # test the count returned

    _logger.info("Running GetCommEventLogRequest")
    rr = client.execute(GetCommEventLogRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert rr.status  # test the status code
    assert not rr.event_count  # test the number of events
    assert not rr.message_count  # test the number of messages
    assert not rr.events  # test the number of events


def execute_diagnostic_requests(client):
    """Execute extended diagnostic requests."""
    _logger.info("### Running ReturnQueryDataRequest")
    rr = client.execute(ReturnQueryDataRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert not rr.message[0]  # test the resulting message

    _logger.info("Running RestartCommunicationsOptionRequest")
    rr = client.execute(RestartCommunicationsOptionRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK
    assert not rr.message[0]  # test the resulting message

    _logger.info("Running ReturnDiagnosticRegisterRequest")
    rr = client.execute(ReturnDiagnosticRegisterRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ChangeAsciiInputDelimiterRequest")
    rr = client.execute(ChangeAsciiInputDelimiterRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ForceListenOnlyModeRequest")
    _logger.info("NOT WORKING")
    _logger.info(str(ForceListenOnlyModeRequest))
    # rr = client.execute(
    #    ForceListenOnlyModeRequest(unit=UNIT)
    # )  # does not send a response
    # assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ClearCountersRequest")
    rr = client.execute(ClearCountersRequest())
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnBusCommunicationErrorCountRequest")
    rr = client.execute(ReturnBusCommunicationErrorCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnBusExceptionErrorCountRequest")
    rr = client.execute(ReturnBusExceptionErrorCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveMessageCountRequest")
    rr = client.execute(ReturnSlaveMessageCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveNoResponseCountRequest")
    rr = client.execute(ReturnSlaveNoResponseCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveNAKCountRequest")
    rr = client.execute(ReturnSlaveNAKCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveBusyCountRequest")
    rr = client.execute(ReturnSlaveBusyCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnSlaveBusCharacterOverrunCountRequest")
    rr = client.execute(ReturnSlaveBusCharacterOverrunCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ReturnIopOverrunCountRequest")
    rr = client.execute(ReturnIopOverrunCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running ClearOverrunCountRequest")
    rr = client.execute(ClearOverrunCountRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK

    _logger.info("Running GetClearModbusPlusRequest")
    rr = client.execute(GetClearModbusPlusRequest(unit=UNIT))
    assert rr and not rr.isError()  # test that calls was OK


def demonstrate_calls(client):
    """Demonstrate basic read/write calls."""
    execute_information_requests(client)
    execute_diagnostic_requests(client)


if __name__ == "__main__":
    testclient = setup_client()
    run_client(testclient, modbus_calls=demonstrate_calls)
