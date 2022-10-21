#!/usr/bin/env python3
"""Pymodbus Asynchronous Client Examples.

The following is an example of how to use the asynchronous serial modbus
client implementation from pymodbus using tornado.
"""
import functools

# ---------------------------------------------------------------------------#
# import needed libraries
# ---------------------------------------------------------------------------#
import logging

from tornado.ioloop import IOLoop

from pymodbus.client.asynchronous import schedulers
from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient


# ---------------------------------------------------------------------------#
# choose the requested modbus protocol
# ---------------------------------------------------------------------------#


# ---------------------------------------------------------------------------#
# configure the client logging
# ---------------------------------------------------------------------------#

FORMAT = (
    "%(asctime)-15s %(threadName)-15s"
    " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

UNIT = 0x01

# ---------------------------------------------------------------------------#
# helper method to test deferred callbacks
# ---------------------------------------------------------------------------#


def dassert(future, callback):
    """Dassert."""

    def _assertor(value):
        # by pass assertion, an error here stops the write callbacks
        assert value  # nosec

    def on_done(f_trans):
        if exc := f_trans.exception():
            log.debug(exc)
            return _assertor(False)

        return _assertor(callback(f_trans.result()))

    future.add_done_callback(on_done)


def _print(value):
    """Print."""
    if hasattr(value, "bits"):
        result = value.bits
    elif hasattr(value, "registers"):
        result = value.registers
    else:
        log.error(value)
        return None
    txt = f"Printing : -- {result}"
    log.info(txt)
    return result


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


def begin_asynchronous_test(client, protocol):
    """Begin async test."""
    rq = client.write_coil(1, True, unit=UNIT)
    rr = client.read_coils(1, 1, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)  # test for no error
    dassert(rr, _print)  # test the expected value

    rq = client.write_coils(1, [False] * 8, unit=UNIT)
    rr = client.read_coils(1, 8, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)  # test for no error
    dassert(rr, _print)  # test the expected value

    rq = client.write_coils(1, [False] * 8, unit=UNIT)
    rr = client.read_discrete_inputs(1, 8, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)  # test for no error
    dassert(rr, _print)  # test the expected value

    rq = client.write_register(1, 10, unit=UNIT)
    rr = client.read_holding_registers(1, 1, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)  # test for no error
    dassert(rr, _print)  # test the expected value

    rq = client.write_registers(1, [10] * 8, unit=UNIT)
    rr = client.read_input_registers(1, 8, unit=UNIT)
    dassert(rq, lambda r: r.function_code < 0x80)  # test for no error
    dassert(rr, _print)  # test the expected value

    arguments = {
        "read_address": 1,
        "read_count": 8,
        "write_address": 1,
        "write_registers": [20] * 8,
    }
    rq = client.readwrite_registers(**arguments, unit=UNIT)
    rr = client.read_input_registers(1, 8, unit=UNIT)
    dassert(rq, lambda r: r.registers == [20] * 8)  # test the expected value
    dassert(rr, _print)  # test the expected value

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
    """Handle error."""
    txt = f"Err {args} {kwargs}"
    log.error(txt)


def callback(protocol, future):
    """Call Callback."""
    log.debug("Client connected")
    if exp := future.exception():
        return err(exp)

    client = future.result()
    return begin_asynchronous_test(client, protocol)


if __name__ == "__main__":
    # ----------------------------------------------------------------------- #
    # Create temporary serial ports using SOCAT

    # socat -d -d PTY,link=/tmp/ptyp0,raw,echo=0,ispeed=9600 PTY,
    # link=/tmp/ttyp0,raw,echo=0,ospeed=9600

    # Default framer is ModbusRtuFramer
    # ----------------------------------------------------------------------- #

    # Rtu
    (
        protocol,
        future,
    ) = AsyncModbusSerialClient(  # pylint: disable=unpacking-non-sequence
        schedulers.IO_LOOP,
        method="rtu",
        port="/tmp/ptyp0",  # nosec
        baudrate=9600,
        timeout=2,
    )

    # Asci
    # from pymodbus.transaction import ModbusAsciiFramer
    # protocol, future = AsyncModbusSerialClient(schedulers.IO_LOOP,
    #                                            method="ascii",
    #                                            port="/dev/ptyp0",
    #                                            framer=ModbusAsciiFramer,
    #                                            baudrate=9600,
    #                                            timeout=2)

    # Binary
    # from pymodbus.transaction import ModbusBinaryFramer
    # protocol, future = AsyncModbusSerialClient(schedulers.IO_LOOP,
    #                                            method="binary",
    #                                            port="/dev/ptyp0",
    #                                            framer=ModbusBinaryFramer,
    #                                            baudrate=9600,
    #                                            timeout=2)
    future.add_done_callback(functools.partial(callback, protocol))
