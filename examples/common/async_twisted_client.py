#!/usr/bin/env python
"""
Pymodbus Asynchronous Client Examples
--------------------------------------------------------------------------

The following is an example of how to use the asynchronous modbus
client implementation from pymodbus.
"""
# --------------------------------------------------------------------------- #
# import needed libraries
# --------------------------------------------------------------------------- #

from twisted.internet import reactor

from pymodbus.client.async.tcp import AsyncModbusTCPClient
# from pymodbus.client.async.udp import AsyncModbusUDPClient
from pymodbus.client.async import schedulers

# --------------------------------------------------------------------------- #
# choose the requested modbus protocol
# --------------------------------------------------------------------------- #

from twisted.internet import reactor, protocol

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# helper method to test deferred callbacks
# --------------------------------------------------------------------------- #


def err(*args, **kwargs):
    logging.error("Err-{}-{}".format(args, kwargs))


def dassert(deferred, callback):
    def _assertor(value):
        assert value
    deferred.addCallback(lambda r: _assertor(callback(r)))
    deferred.addErrback(err)

# --------------------------------------------------------------------------- #
# specify slave to query
# --------------------------------------------------------------------------- #
# The slave to query is specified in an optional parameter for each
# individual request. This can be done by specifying the `unit` parameter
# which defaults to `0x00`
# --------------------------------------------------------------------------- #


UNIT = 0x01


def processResponse(result):
    log.debug(result)


def exampleRequests(client):
    rr = client.read_coils(1, 1, unit=0x02)
    rr.addCallback(processResponse)
    rr = client.read_holding_registers(1, 1, unit=0x02)
    rr.addCallback(processResponse)
    rr = client.read_discrete_inputs(1, 1, unit=0x02)
    rr.addCallback(processResponse)
    rr = client.read_input_registers(1, 1, unit=0x02)
    rr.addCallback(processResponse)
    stopAsynchronousTest(client)

# --------------------------------------------------------------------------- #
# example requests
# --------------------------------------------------------------------------- #
# simply call the methods that you would like to use. An example session
# is displayed below along with some assert checks. Note that unlike the
# synchronous version of the client, the asynchronous version returns
# deferreds which can be thought of as a handle to the callback to send
# the result of the operation.  We are handling the result using the
# deferred assert helper(dassert).
# --------------------------------------------------------------------------- #


def stopAsynchronousTest(client):
    # ----------------------------------------------------------------------- #
    # close the client at some time later
    # ----------------------------------------------------------------------- #
    reactor.callLater(1, client.transport.loseConnection)
    reactor.callLater(2, reactor.stop)


def beginAsynchronousTest(client):
    rq = client.write_coil(1, True, unit=UNIT)
    rr = client.read_coils(1, 1, unit=UNIT)
    dassert(rq, lambda r: not r.isError())     # test for no error
    dassert(rr, lambda r: r.bits[0] == True)          # test the expected value

    rq = client.write_coils(1, [True]*8, unit=UNIT)
    rr = client.read_coils(1, 8, unit=UNIT)
    dassert(rq, lambda r: not r.isError())     # test for no error
    dassert(rr, lambda r: r.bits == [True]*8)        # test the expected value

    rq = client.write_coils(1, [False]*8, unit=UNIT)
    rr = client.read_discrete_inputs(1, 8, unit=UNIT)
    dassert(rq, lambda r: not r.isError())     # test for no error
    dassert(rr, lambda r: r.bits == [True]*8)        # test the expected value

    rq = client.write_register(1, 10, unit=UNIT)
    rr = client.read_holding_registers(1, 1, unit=UNIT)
    dassert(rq, lambda r: not r.isError())     # test for no error
    dassert(rr, lambda r: r.registers[0] == 10)       # test the expected value

    rq = client.write_registers(1, [10]*8, unit=UNIT)
    rr = client.read_input_registers(1, 8, unit=UNIT)
    dassert(rq, lambda r: not r.isError())     # test for no error
    dassert(rr, lambda r: r.registers == [17]*8)      # test the expected value

    arguments = {
        'read_address':    1,
        'read_count':      8,
        'write_address':   1,
        'write_registers': [20]*8,
    }
    rq = client.readwrite_registers(arguments, unit=UNIT)
    rr = client.read_input_registers(1, 8, unit=UNIT)
    dassert(rq, lambda r: r.registers == [20]*8)      # test the expected value
    dassert(rr, lambda r: r.registers == [17]*8)      # test the expected value
    stopAsynchronousTest(client)

    # ----------------------------------------------------------------------- #
    # close the client at some time later
    # ----------------------------------------------------------------------- #
    # reactor.callLater(1, client.transport.loseConnection)
    reactor.callLater(2, reactor.stop)

# --------------------------------------------------------------------------- #
# extra requests
# --------------------------------------------------------------------------- #
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
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# choose the client you want
# --------------------------------------------------------------------------- #
# make sure to start an implementation to hit against. For this
# you can use an existing device, the reference implementation in the tools
# directory, or start a pymodbus server.
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    protocol, deferred = AsyncModbusTCPClient(schedulers.REACTOR, port=5020)
    # protocol, deferred = AsyncModbusUDPClient(schedulers.REACTOR, port=5020)
                             # callback=beginAsynchronousTest,
                             # errback=err)
    deferred.addCallback(beginAsynchronousTest)
    deferred.addErrback(err)
