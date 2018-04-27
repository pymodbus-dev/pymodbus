#!/usr/bin/env python
"""
Pymodbus Synchronous Client Extended Examples
--------------------------------------------------------------------------

The following is an example of how to use the synchronous modbus client
implementation from pymodbus to perform the extended portions of the
modbus protocol.
"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
# from pymodbus.client.sync import ModbusTcpClient as ModbusClient
# from pymodbus.client.sync import ModbusUdpClient as ModbusClient
from pymodbus.client.sync import ModbusSerialClient as ModbusClient


# --------------------------------------------------------------------------- # 
# import the extended messages to perform
# --------------------------------------------------------------------------- #
from pymodbus.diag_message import *
from pymodbus.file_message import *
from pymodbus.other_message import *
from pymodbus.mei_message import *

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

UNIT = 0x01


def execute_extended_requests():
    # ------------------------------------------------------------------------#
    # choose the client you want
    # ------------------------------------------------------------------------#
    # make sure to start an implementation to hit against. For this
    # you can use an existing device, the reference implementation in the tools
    # directory, or start a pymodbus server.
    #
    # It should be noted that you can supply an ipv4 or an ipv6 host address
    # for both the UDP and TCP clients.
    # ------------------------------------------------------------------------# 
    client = ModbusClient(method='rtu', port="/dev/ptyp0")
    # client = ModbusClient(method='ascii', port="/dev/ptyp0")
    # client = ModbusClient(method='binary', port="/dev/ptyp0")
    # client = ModbusClient('127.0.0.1', port=5020)
    # from pymodbus.transaction import ModbusRtuFramer
    # client = ModbusClient('127.0.0.1', port=5020, framer=ModbusRtuFramer)
    client.connect()

    # ----------------------------------------------------------------------- #
    # extra requests
    # ----------------------------------------------------------------------- #
    # If you are performing a request that is not available in the client
    # mixin, you have to perform the request like this instead::
    #
    # from pymodbus.diag_message import ClearCountersRequest
    # from pymodbus.diag_message import ClearCountersResponse
    #
    # request  = ClearCountersRequest()
    # response = client.execute(request)
    # if isinstance(response, ClearCountersResponse):
    #     ... do something with the response
    #
    #
    # What follows is a listing of all the supported methods. Feel free to
    # comment, uncomment, or modify each result set to match with your ref.
    # ----------------------------------------------------------------------- #

    # ----------------------------------------------------------------------- #
    # information requests
    # ----------------------------------------------------------------------- #
    log.debug("Running ReadDeviceInformationRequest")
    rq = ReadDeviceInformationRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)              # not supported by reference
    # assert (not rr.isError())  # test that we are not an error
    # assert (rr.information[0] == b'Pymodbus')  # test the vendor name
    # assert (rr.information[1] == b'PM')  # test the product code
    # assert (rr.information[2] == b'1.0')  # test the code revision

    log.debug("Running ReportSlaveIdRequest")
    rq = ReportSlaveIdRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                        # not supported by reference
    # assert(not rr.isError())           # test that we are not an error
    # assert(rr.identifier  == 0x00)            # test the slave identifier
    # assert(rr.status  == 0x00)                # test that the status is ok

    log.debug("Running ReadExceptionStatusRequest")
    rq = ReadExceptionStatusRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                        # not supported by reference
    # assert(not rr.isError())           # test that we are not an error
    # assert(rr.status == 0x55)                 # test the status code

    log.debug("Running GetCommEventCounterRequest")
    rq = GetCommEventCounterRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                       # not supported by reference
    # assert(not rr.isError())          # test that we are not an error
    # assert(rr.status == True)                # test the status code
    # assert(rr.count == 0x00)                 # test the status code

    log.debug("Running GetCommEventLogRequest")
    rq = GetCommEventLogRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                       # not supported by reference
    # assert(not rr.isError())          # test that we are not an error
    # assert(rr.status == True)                # test the status code
    # assert(rr.event_count == 0x00)           # test the number of events
    # assert(rr.message_count == 0x00)         # test the number of messages
    # assert(len(rr.events) == 0x00)           # test the number of events

    # ------------------------------------------------------------------------#
    # diagnostic requests
    # ------------------------------------------------------------------------#
    log.debug("Running ReturnQueryDataRequest")
    rq = ReturnQueryDataRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                      # not supported by reference
    # assert(rr.message[0] == 0x0000)         # test the resulting message

    log.debug("Running RestartCommunicationsOptionRequest")
    rq = RestartCommunicationsOptionRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                     # not supported by reference
    # assert(rr.message == 0x0000)           # test the resulting message

    log.debug("Running ReturnDiagnosticRegisterRequest")
    rq = ReturnDiagnosticRegisterRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                     # not supported by reference

    log.debug("Running ChangeAsciiInputDelimiterRequest")
    rq = ChangeAsciiInputDelimiterRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                    # not supported by reference

    log.debug("Running ForceListenOnlyModeRequest")
    rq = ForceListenOnlyModeRequest(unit=UNIT)
    rr = client.execute(rq)  # does not send a response
    log.debug(rr)

    log.debug("Running ClearCountersRequest")
    rq = ClearCountersRequest()
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                   # not supported by reference

    log.debug("Running ReturnBusCommunicationErrorCountRequest")
    rq = ReturnBusCommunicationErrorCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                    # not supported by reference

    log.debug("Running ReturnBusExceptionErrorCountRequest")
    rq = ReturnBusExceptionErrorCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                   # not supported by reference

    log.debug("Running ReturnSlaveMessageCountRequest")
    rq = ReturnSlaveMessageCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                  # not supported by reference

    log.debug("Running ReturnSlaveNoResponseCountRequest")
    rq = ReturnSlaveNoResponseCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)                  # not supported by reference

    log.debug("Running ReturnSlaveNAKCountRequest")
    rq = ReturnSlaveNAKCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)               # not supported by reference

    log.debug("Running ReturnSlaveBusyCountRequest")
    rq = ReturnSlaveBusyCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)               # not supported by reference

    log.debug("Running ReturnSlaveBusCharacterOverrunCountRequest")
    rq = ReturnSlaveBusCharacterOverrunCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)               # not supported by reference

    log.debug("Running ReturnIopOverrunCountRequest")
    rq = ReturnIopOverrunCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)               # not supported by reference

    log.debug("Running ClearOverrunCountRequest")
    rq = ClearOverrunCountRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)               # not supported by reference

    log.debug("Running GetClearModbusPlusRequest")
    rq = GetClearModbusPlusRequest(unit=UNIT)
    rr = client.execute(rq)
    log.debug(rr)
    # assert(rr == None)               # not supported by reference

    # ------------------------------------------------------------------------#
    # close the client
    # ------------------------------------------------------------------------#
    client.close()


if __name__ == "__main__":
    execute_extended_requests()





