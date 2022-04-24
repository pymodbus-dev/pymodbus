#!/usr/bin/env python3
""" Pymodbus Asynchronous Client Examples
--------------------------------------------------------------------------

The following is an example of how to use the asynchronous modbus
client implementation from pymodbus with asyncio.

The example is only valid on Python3.4 and above
"""
# pylint: disable=R0801
import asyncio
import logging
import time
from threading import Thread

# ----------------------------------------------------------------------- #
# Import the required asynchronous client
# ----------------------------------------------------------------------- #
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
# from pymodbus.client.asynchronous.udp import (
#     AsyncModbusUDPClient as ModbusClient)
from pymodbus.client.asynchronous import schedulers


# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #

_logger = logging.getLogger()
_logger.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# specify slave to query
# --------------------------------------------------------------------------- #
# The slave to query is specified in an optional parameter for each
# individual request. This can be done by specifying the `unit` parameter
# which defaults to `0x00`
# --------------------------------------------------------------------------- #


UNIT = 0x01


async def start_async_test(client):
    """ Start async test. """
    # ----------------------------------------------------------------------- #
    # specify slave to query
    # ----------------------------------------------------------------------- #
    # The slave to query is specified in an optional parameter for each
    # individual request. This can be done by specifying the `unit` parameter
    # which defaults to `0x00`
    # ----------------------------------------------------------------------- #
    _logger.debug("Reading Coils")
    rr = await client.read_coils(1, 1, unit=0x01)

    # ----------------------------------------------------------------------- #
    # example requests
    # ----------------------------------------------------------------------- #
    # simply call the methods that you would like to use. An example session
    # is displayed below along with some assert checks. Note that some modbus
    # implementations differentiate holding/input discrete/coils and as such
    # you will not be able to write to these, therefore the starting values
    # are not known to these tests. Furthermore, some use the same memory
    # blocks for the two sets, so a change to one is a change to the other.
    # Keep both of these cases in mind when testing as the following will
    # _only_ pass with the supplied asynchronous modbus server (script supplied).
    # ----------------------------------------------------------------------- #
    _logger.debug("Write to a Coil and read back")
    rq = await client.write_coil(0, True, unit=UNIT)
    rr = await client.read_coils(0, 1, unit=UNIT)
    assert rq.function_code < 0x80     # test that we are not an error
    assert rr.bits[0]          # test the expected value

    _logger.debug("Write to multiple coils and read back- test 1")
    rq = await client.write_coils(1, [True] * 8, unit=UNIT)
    assert rq.function_code < 0x80     # test that we are not an error
    rr = await client.read_coils(1, 21, unit=UNIT)
    assert rr.function_code < 0x80     # test that we are not an error
    resp = [True] * 21

    # If the returned output quantity is not a multiple of eight,
    # the remaining bits in the final data byte will be padded with zeros
    # (toward the high order end of the byte).

    resp.extend([False] * 3)
    assert rr.bits == resp         # test the expected value

    _logger.debug("Write to multiple coils and read back - test 2")
    rq = await client.write_coils(1, [False] * 8, unit=UNIT)
    rr = await client.read_coils(1, 8, unit=UNIT)
    assert rq.function_code < 0x80     # test that we are not an error
    assert rr.bits == [False] * 8         # test the expected value

    _logger.debug("Read discrete inputs")
    rr = await client.read_discrete_inputs(0, 8, unit=UNIT)
    assert rq.function_code < 0x80     # test that we are not an error

    _logger.debug("Write to a holding register and read back")
    rq = await client.write_register(1, 10, unit=UNIT)
    rr = await client.read_holding_registers(1, 1, unit=UNIT)
    assert rq.function_code < 0x80     # test that we are not an error
    assert rr.registers[0] == 10       # test the expected value

    _logger.debug("Write to multiple holding registers and read back")
    rq = await client.write_registers(1, [10] * 8, unit=UNIT)
    rr = await client.read_holding_registers(1, 8, unit=UNIT)
    assert rq.function_code < 0x80      # test that we are not an error
    assert rr.registers == [10] * 8       # test the expected value

    _logger.debug("Read input registers")
    rr = await client.read_input_registers(1, 8, unit=UNIT)
    assert rq.function_code < 0x80      # test that we are not an error

    arguments = {
        'read_address': 1,
        'read_count': 8,
        'write_address': 1,
        'write_registers': [20] * 8,
    }
    _logger.debug("Read write registeres simulataneously")
    rq = await client.readwrite_registers(unit=UNIT, **arguments)
    rr = await client.read_holding_registers(1, 8, unit=UNIT)
    assert rq.function_code < 0x80     # test that we are not an error
    assert rq.registers == [20] * 8      # test the expected value
    assert rr.registers == [20] * 8     # test the expected value
    await asyncio.sleep(1)


def run_with_not_running_loop():
    """ A loop is created and is passed to ModbusClient factory to be used. """
    _logger.debug("Running Async client with asyncio loop not yet started")
    _logger.debug("------------------------------------------------------")
    loop = asyncio.new_event_loop()
    assert not loop.is_running()
    asyncio.set_event_loop(loop)
    new_loop, client = ModbusClient(schedulers.ASYNC_IO, port=5020, loop=loop) #NOSONAR pylint: disable=unpacking-non-sequence,unused-variable
    loop.run_until_complete(start_async_test(client.protocol))
    loop.close()
    _logger.debug("--------------RUN_WITH_NOT_RUNNING_LOOP---------------")
    _logger.debug("")


async def run_with_already_running_loop():
    """ An already running loop is passed to ModbusClient Factory. """
    _logger.debug("Running Async client with asyncio loop already started")
    _logger.debug("------------------------------------------------------")

    def done(future): # pylint: disable=unused-argument
        """ Done. """
        _logger.info("Done !!!")

    def start_loop(loop):
        """ Start Loop
        :param loop:
        :return:
        """
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop = asyncio.new_event_loop()
    mythread = Thread(target=start_loop, args=[loop])
    mythread.daemon = True
    # Start the loop
    mythread.start()
    asyncio.sleep(1)
    assert loop.is_running()
    asyncio.set_event_loop(loop)
    loop, client = ModbusClient(schedulers.ASYNC_IO, port=5020, loop=loop) #NOSONAR pylint: disable=unpacking-non-sequence
    future = asyncio.run_coroutine_threadsafe(
        start_async_test(client.protocol), loop=loop)
    future.add_done_callback(done)
    while not future.done():
        time.sleep(0.1)
    loop.stop()
    _logger.debug("--------DONE RUN_WITH_ALREADY_RUNNING_LOOP-------------")
    _logger.debug("")


def run_with_no_loop():
    """ ModbusClient Factory creates a loop.
    :return:
    """
    _logger.debug("---------------------RUN_WITH_NO_LOOP-----------------")
    loop, client = ModbusClient(schedulers.ASYNC_IO, port=5020) #NOSONAR pylint: disable=unpacking-non-sequence
    loop.run_until_complete(start_async_test(client.protocol))
    loop.close()
    _logger.debug("--------DONE RUN_WITH_NO_LOOP-------------")
    _logger.debug("")


if __name__ == '__main__':
    # Run with No loop
    _logger.debug("Running Async client")
    _logger.debug("------------------------------------------------------")
    # run_with_no_loop()

    # Run with loop not yet started
    # run_with_not_running_loop()

    # Run with already running loop
    asyncio.run(run_with_already_running_loop())

    _logger.debug("")
