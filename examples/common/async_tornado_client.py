#!/usr/bin/env python
"""
Pymodbus Asynchronous Client Examples
--------------------------------------------------------------------------

The following is an example of how to use the asynchronous modbus
client implementation from pymodbus using Tornado.
"""

import functools
from tornado.ioloop import IOLoop
from pymodbus.client.async import schedulers

# ---------------------------------------------------------------------------#
# choose the requested modbus protocol
# ---------------------------------------------------------------------------#

# from pymodbus.client.async.udp import AsyncModbusUDPClient as ModbusClient
from pymodbus.client.async.tcp import AsyncModbusTCPClient as ModbusClient

# ---------------------------------------------------------------------------#
# configure the client logging
# ---------------------------------------------------------------------------#
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------#
# helper method to test deferred callbacks
# ---------------------------------------------------------------------------#


def dassert(future, callback):

    def _assertor(value):
        # by pass assertion, an error here stops the write callbacks
        assert value

    def on_done(f):
        exc = f.exception()
        if exc:
            log.debug(exc)
            return _assertor(False)

        return _assertor(callback(f.result()))

    future.add_done_callback(on_done)


def _print(value):
    if hasattr(value, "bits"):
        t = value.bits
    elif hasattr(value, "registers"):
        t = value.registers
    else:
        log.error(value)
        return
    log.info("Printing : -- {}".format(t))
    return t


UNIT = 0x01

# ---------------------------------------------------------------------------#
# example requests
# ---------------------------------------------------------------------------#
# simply call the methods that you would like to use. An example session
# is displayed below along with some assert checks. Note that unlike the
# synchronous version of the client, the asynchronous version returns
# deferreds which can be thought of as a handle to the callback to send
# the result of the operation.  We are handling the result using the
# deferred assert helper(dassert).
# ---------------------------------------------------------------------------#


def beginAsynchronousTest(client, protocol):
    rq = client.write_coil(1, True, unit=UNIT)
    rr = client.read_coils(1, 1, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)     # test for no error
    dassert(rr, _print)          # test the expected value

    rq = client.write_coils(1, [False]*8, unit=UNIT)
    rr = client.read_coils(1, 8, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)     # test for no error
    dassert(rr, _print)         # test the expected value

    rq = client.write_coils(1, [False]*8, unit=UNIT)
    rr = client.read_discrete_inputs(1, 8, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)     # test for no error
    dassert(rr, _print)         # test the expected value

    rq = client.write_register(1, 10, unit=UNIT)
    rr = client.read_holding_registers(1, 1, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)     # test for no error
    dassert(rr, _print)       # test the expected value

    rq = client.write_registers(1, [10]*8, unit=UNIT)
    rr = client.read_input_registers(1, 8, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)     # test for no error
    dassert(rr, _print)      # test the expected value

    arguments = {
        'read_address':    1,
        'read_count':      8,
        'write_address':   1,
        'write_registers': [20]*8,
    }
    rq = client.readwrite_registers(**arguments, unit=UNIT)
    rr = client.read_input_registers(1,8, unit=UNIT)
    dassert(rq, lambda r: r.registers == [20]*8)      # test the expected value
    dassert(rr, _print)      # test the expected value

    # -----------------------------------------------------------------------#
    # close the client at some time later
    # -----------------------------------------------------------------------#
    IOLoop.current().add_timeout(IOLoop.current().time() + 1, client.close)
    IOLoop.current().add_timeout(IOLoop.current().time() + 2, protocol.stop)

# ---------------------------------------------------------------------------#
# choose the client you want
# ---------------------------------------------------------------------------#
# make sure to start an implementation to hit against. For this
# you can use an existing device, the reference implementation in the tools
# directory, or start a pymodbus server.
# ---------------------------------------------------------------------------#


def err(*args, **kwargs):
    log.error("Err", args, kwargs)


def callback(protocol, future):
    log.debug("Client connected")
    exp = future.exception()
    if exp:
        return err(exp)

    client = future.result()
    return beginAsynchronousTest(client, protocol)


if __name__ == "__main__":
    protocol, future = ModbusClient(schedulers.IO_LOOP, port=5020)
    future.add_done_callback(functools.partial(callback, protocol))



