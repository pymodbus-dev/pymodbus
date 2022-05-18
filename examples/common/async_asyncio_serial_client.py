#!/usr/bin/env python3
"""Pymodbus Asynchronous Client Examples.

The following is an example of how to use the asynchronous serial modbus
client implementation from pymodbus with asyncio.

The example is only valid on Python3.4 and above
"""
import logging
import asyncio
from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient as ModbusClient
from pymodbus.client.asynchronous import schedulers


# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
log = logging.getLogger()
log.setLevel(logging.DEBUG)


# --------------------------------------------------------------------------- #
# specify slave to query
# --------------------------------------------------------------------------- #
# The slave to query is specified in an optional parameter for each
# individual request. This can be done by specifying the `unit` parameter
# which defaults to `0x00`
# --------------------------------------------------------------------------- #


UNIT = 0x01


async def start_async_test(client):  # pylint: disable=redefined-outer-name
    """Start async test."""
    # ----------------------------------------------------------------------- #
    # specify slave to query
    # ----------------------------------------------------------------------- #
    # The slave to query is specified in an optional parameter for each
    # individual request. This can be done by specifying the `unit` parameter
    # which defaults to `0x00`
    # ----------------------------------------------------------------------- #
    try:
        # ----------------------------------------------------------------------- #
        # example requests
        # ----------------------------------------------------------------------- #
        # simply call the methods that you would like to use.
        # An example session is displayed below along with some assert checks.
        # Note that some modbus implementations differentiate holding/
        # input discrete/coils and as such you will not be able to write to
        # these, therefore the starting values are not known to these tests.
        # Furthermore, some use the same memory blocks for the two sets,
        # so a change to one is a change to the other.
        # Keep both of these cases in mind when testing as the following will
        # _only_ pass with the supplied asynchronous modbus server (script supplied).
        # ----------------------------------------------------------------------- #
        log.debug("Write to a Coil and read back")
        rq = await client.write_coil(0, True, unit=UNIT)
        rr = await client.read_coils(0, 1, unit=UNIT)

        assert rq.function_code < 0x80  # nosec test that we are not an error
        assert rr.bits[0]  # nosec test the expected value

        log.debug("Write to multiple coils and read back- test 1")
        rq = await client.write_coils(1, [True] * 8, unit=UNIT)
        rr = await client.read_coils(1, 21, unit=UNIT)

        assert rq.function_code < 0x80  # nosec test that we are not an error
        assert rr.function_code < 0x80  # nosec test that we are not an error

        # If the returned output quantity is not a multiple of eight,
        # the remaining bits in the final data byte will be padded with zeros
        # (toward the high order end of the byte).

        resp = [True] * 21
        resp.extend([False] * 3)
        assert rr.bits == resp  # nosec test the expected value

        log.debug("Write to multiple coils and read back - test 2")
        rq = await client.write_coils(1, [False] * 8, unit=UNIT)
        rr = await client.read_coils(1, 8, unit=UNIT)
        assert rq.function_code < 0x80  # nosec test that we are not an error
        assert rr.bits == [False] * 8  # nosec test the expected value

        log.debug("Read discrete inputs")
        rr = await client.read_discrete_inputs(0, 8, unit=UNIT)
        assert rq.function_code < 0x80  # nosec test that we are not an error

        log.debug("Write to a holding register and read back")
        rq = await client.write_register(1, 10, unit=UNIT)
        rr = await client.read_holding_registers(1, 1, unit=UNIT)
        assert rq.function_code < 0x80  # nosec test that we are not an error
        assert rr.registers[0] == 10  # nosec test the expected value

        log.debug("Write to multiple holding registers and read back")
        rq = await client.write_registers(1, [10] * 8, unit=UNIT)
        rr = await client.read_holding_registers(1, 8, unit=UNIT)
        assert rq.function_code < 0x80  # nosec test that we are not an error
        assert rr.registers == [10] * 8  # nosec test the expected value

        log.debug("Read input registers")
        rr = await client.read_input_registers(1, 8, unit=UNIT)
        assert rq.function_code < 0x80  # nosec test that we are not an error

        arguments = {
            "read_address": 1,
            "read_count": 8,
            "write_address": 1,
            "write_registers": [20] * 8,
        }
        log.debug("Read write registers simultaneously")
        rq = await client.readwrite_registers(unit=UNIT, **arguments)
        rr = await client.read_holding_registers(1, 8, unit=UNIT)
        assert rq.function_code < 0x80  # nosec test that we are not an error
        assert rq.registers == [20] * 8  # nosec test the expected value
        assert rr.registers == [20] * 8  # nosec test the expected value
    except Exception as exc:  # pylint: disable=broad-except
        log.exception(exc)
        client.transport.close()
    await asyncio.sleep(1)


if __name__ == "__main__":
    # ----------------------------------------------------------------------- #
    # For testing on linux based systems you can use socat to create serial
    # ports
    # ----------------------------------------------------------------------- #
    # socat -d -d PTY,link=/tmp/ptyp0,raw,echo=0,ispeed=9600 PTY,
    # link=/tmp/ttyp0,raw,echo=0,ospeed=9600
    loop, client = ModbusClient(  # NOSONAR # pylint: disable=unpacking-non-sequence
        schedulers.ASYNC_IO,
        port="/tmp/ttyp0",  # NOSONAR # nosec
        baudrate=9600,
        method="rtu",
    )
    loop.run_until_complete(start_async_test(client.protocol))
    loop.close()
