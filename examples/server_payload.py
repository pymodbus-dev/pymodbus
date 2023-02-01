#!/usr/bin/env python3
"""Pymodbus Server Payload Example.

This example shows how to initialize a server with a
complicated memory layout using builder.
"""
import asyncio
import logging

from examples.helper import get_commandline
from examples.server_async import run_async_server, setup_server
from pymodbus import pymodbus_apply_logging_config
from pymodbus.constants import Endian
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.payload import BinaryPayloadBuilder


_logger = logging.getLogger()


def setup_payload_server(args):
    """Define payload for server and do setup."""

    pymodbus_apply_logging_config()
    _logger.setLevel(logging.DEBUG)

    # ----------------------------------------------------------------------- #
    # build your payload
    # ----------------------------------------------------------------------- #
    builder = BinaryPayloadBuilder(byteorder=Endian.Little, wordorder=Endian.Little)
    builder.add_string("abcdefgh")
    builder.add_bits([0, 1, 0, 1, 1, 0, 1, 0])
    builder.add_8bit_int(-0x12)
    builder.add_8bit_uint(0x12)
    builder.add_16bit_int(-0x5678)
    builder.add_16bit_uint(0x1234)
    builder.add_32bit_int(-0x1234)
    builder.add_32bit_uint(0x12345678)
    builder.add_16bit_float(12.34)
    builder.add_16bit_float(-12.34)
    builder.add_32bit_float(22.34)
    builder.add_32bit_float(-22.34)
    builder.add_64bit_int(-0xDEADBEEF)
    builder.add_64bit_uint(0x12345678DEADBEEF)
    builder.add_64bit_uint(0xDEADBEEFDEADBEED)
    builder.add_64bit_float(123.45)
    builder.add_64bit_float(-123.45)

    # ----------------------------------------------------------------------- #
    # use that payload in the data store
    # Here we use the same reference block for each underlying store.
    # ----------------------------------------------------------------------- #

    block = ModbusSequentialDataBlock(1, builder.to_registers())
    store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    args.context = ModbusServerContext(slaves=store, single=True)
    return setup_server(args)


if __name__ == "__main__":
    cmd_args = get_commandline(
        server=True,
        description="Run payload server.",
    )
    run_args = setup_payload_server(cmd_args)
    asyncio.run(run_async_server(run_args))
