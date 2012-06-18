#!/usr/bin/env python
'''
Pymodbus Synchronous Client Extended Examples
--------------------------------------------------------------------------

The following is an example of how to use the synchronous modbus client
implementation from pymodbus to perform the extended portions of the
modbus protocol.
'''
#---------------------------------------------------------------------------# 
# import the various server implementations
#---------------------------------------------------------------------------# 
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
#from pymodbus.client.sync import ModbusUdpClient as ModbusClient
#from pymodbus.client.sync import ModbusSerialClient as ModbusClient

#---------------------------------------------------------------------------# 
# configure the client logging
#---------------------------------------------------------------------------# 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#---------------------------------------------------------------------------# 
# choose the client you want
#---------------------------------------------------------------------------# 
# make sure to start an implementation to hit against. For this
# you can use an existing device, the reference implementation in the tools
# directory, or start a pymodbus server.
#
# It should be noted that you can supply an ipv4 or an ipv6 host address for
# both the UDP and TCP clients.
#---------------------------------------------------------------------------# 
client = ModbusClient('127.0.0.1')
client.connect()

#---------------------------------------------------------------------------# 
# import the extended messages to perform
#---------------------------------------------------------------------------# 
from pymodbus.diag_message import *
from pymodbus.file_message import *
from pymodbus.other_message import *
from pymodbus.mei_message import *

#---------------------------------------------------------------------------# 
# extra requests
#---------------------------------------------------------------------------# 
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
# comment, uncomment, or modify each result set to match with your reference.
#---------------------------------------------------------------------------# 

#---------------------------------------------------------------------------# 
# information requests
#---------------------------------------------------------------------------# 
rq = ReadDeviceInformationRequest()
rr = client.execute(rq)
#assert(rr == None)                             # not supported by reference
assert(rr.function_code < 0x80)                 # test that we are not an error
assert(rr.information[0] == 'proconX Pty Ltd')  # test the vendor name
assert(rr.information[1] == 'FT-MBSV')          # test the product code
assert(rr.information[2] == 'EXPERIMENTAL')     # test the code revision

rq = ReportSlaveIdRequest()
rr = client.execute(rq)
assert(rr == None)                              # not supported by reference
#assert(rr.function_code < 0x80)                # test that we are not an error
#assert(rr.identifier  == 0x00)                 # test the slave identifier
#assert(rr.status  == 0x00)                     # test that the status is ok

rq = ReadExceptionStatusRequest()
rr = client.execute(rq)
#assert(rr == None)                             # not supported by reference
assert(rr.function_code < 0x80)                 # test that we are not an error
assert(rr.status == 0x55)                       # test the status code

rq = GetCommEventCounterRequest()
rr = client.execute(rq)
assert(rr == None)                              # not supported by reference
#assert(rr.function_code < 0x80)                # test that we are not an error
#assert(rr.status == True)                      # test the status code
#assert(rr.count == 0x00)                       # test the status code

rq = GetCommEventLogRequest()
rr = client.execute(rq)
#assert(rr == None)                             # not supported by reference
#assert(rr.function_code < 0x80)                # test that we are not an error
#assert(rr.status == True)                      # test the status code
#assert(rr.event_count == 0x00)                 # test the number of events
#assert(rr.message_count == 0x00)               # test the number of messages
#assert(len(rr.events) == 0x00)                 # test the number of events

#---------------------------------------------------------------------------# 
# diagnostic requests
#---------------------------------------------------------------------------# 
rq = ReturnQueryDataRequest()
rr = client.execute(rq)
assert(rr == None)                             # not supported by reference
#assert(rr.message[0] == 0x0000)               # test the resulting message

rq = RestartCommunicationsOptionRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference
#assert(rr.message == 0x0000)                  # test the resulting message

rq = ReturnDiagnosticRegisterRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ChangeAsciiInputDelimiterRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ForceListenOnlyModeRequest()
client.execute(rq)                             # does not send a response

rq = ClearCountersRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ReturnBusCommunicationErrorCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ReturnBusExceptionErrorCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ReturnSlaveMessageCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ReturnSlaveNoResponseCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ReturnSlaveNAKCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ReturnSlaveBusyCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ReturnSlaveBusCharacterOverrunCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ReturnIopOverrunCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = ClearOverrunCountRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

rq = GetClearModbusPlusRequest()
rr = client.execute(rq)
#assert(rr == None)                            # not supported by reference

#---------------------------------------------------------------------------# 
# close the client
#---------------------------------------------------------------------------# 
client.close()
