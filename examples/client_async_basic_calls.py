#!/usr/bin/env python3
"""Pymodbus Asynchronous Client standard calls example.

This example uses client_async.py to handle connection, and have the same options.

The corresponding server must be started before e.g. as:
    python3 server_sync.py
"""
import asyncio
import logging

from examples.client_async import run_async_client, setup_async_client


SLAVE = 0x01


async def _handle_coils(client):
    """Read/Write coils."""
    _logger.info("### Reading Coil")
    rr = await client.read_coils(1, 1, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)

    _logger.info("### Reading Coils to get bit 5")
    rr = await client.read_coils(1, 5, slave=SLAVE)
    assert not rr.isError()  # test that call was OK
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)

    _logger.info("### Write true to coil bit 0 and read to verify")
    rq = await client.write_coil(0, True, slave=SLAVE)
    rr = await client.read_coils(0, 1, slave=SLAVE)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rr.bits[0]  # test the expected value
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)

    _logger.info("### Write true to multiple coils 1-8")
    rq = await client.write_coils(1, [True] * 21, slave=SLAVE)
    rr = await client.read_coils(1, 21, slave=SLAVE)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    resp = [True] * 21
    # If the returned output quantity is not a multiple of eight,
    # the remaining bits in the final data byte will be padded with zeros
    # (toward the high order end of the byte).
    resp.extend([False] * 3)
    assert rr.bits == resp  # test the expected value
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)

    _logger.info("### Write False to address 1-8 coils")
    rq = await client.write_coils(1, [False] * 8, slave=SLAVE)
    rr = await client.read_coils(1, 8, slave=SLAVE)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rr.bits == [False] * 8  # test the expected value
    txt = f"### coils response: {str(rr.bits)}"
    _logger.debug(txt)


async def _handle_discrete_input(client):
    """Read discrete inputs."""
    _logger.info("### Reading discrete input, Read address:0-7")
    rr = await client.read_discrete_inputs(0, 8, slave=SLAVE)
    assert not rr.isError()  # nosec test that we are not an error
    txt = f"### address 0-7 is: {str(rr.bits)}"
    _logger.debug(txt)


async def _handle_holding_registers(client):
    """Read/write holding registers."""
    _logger.info("### write holding register and read holding registers")
    rq = await client.write_register(1, 10, slave=SLAVE)
    rr = await client.read_holding_registers(1, 1, slave=SLAVE)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rr.registers[0] == 10  # nosec test the expected value
    txt = f"### address 1 is: {str(rr.registers[0])}"
    _logger.debug(txt)

    _logger.info("### write holding registers and read holding registers")
    rq = await client.write_registers(1, [10] * 8, slave=SLAVE)
    rr = await client.read_holding_registers(1, 8, slave=SLAVE)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rr.registers == [10] * 8  # nosec test the expected value
    txt = f"### address 1-8 is: {str(rr.registers)}"
    _logger.debug(txt)

    _logger.info("### write read holding registers")
    arguments = {
        "read_address": 1,
        "read_count": 8,
        "write_address": 1,
        "write_registers": [256, 128, 100, 50, 25, 10, 5, 1],
    }
    rq = await client.readwrite_registers(unit=SLAVE, **arguments)
    rr = await client.read_holding_registers(1, 8, slave=SLAVE)
    assert not rq.isError() and not rr.isError()  # test that calls was OK
    assert rq.registers == arguments["write_registers"]
    assert rr.registers == arguments["write_registers"]
    txt = f"### Test 8 read result: address 1-8 is: {str(rr.registers)}"
    _logger.debug(txt)


async def _handle_input_registers(client):
    """Read input registers."""
    _logger.info("### read input registers")
    rr = await client.read_input_registers(1, 8, slave=SLAVE)
    assert not rr.isError()  # nosec test that we are not an error
    txt = f"### address 1 is: {str(rr.registers[0])}"
    _logger.debug(txt)


async def run_async_basic_calls(client):
    """Demonstrate basic read/write calls."""
    await _handle_coils(client)
    await _handle_discrete_input(client)
    await _handle_holding_registers(client)
    await _handle_input_registers(client)

# --------------------------------------------------------------------------- #
# Extra code, to allow commandline parameters instead of changing the code
# --------------------------------------------------------------------------- #
FORMAT = "%(asctime)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
logging.basicConfig(format=FORMAT)
_logger = logging.getLogger()


if __name__ == "__main__":
    testclient = setup_async_client()
    asyncio.run(run_async_client(testclient, modbus_calls=run_async_basic_calls))
