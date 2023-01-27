#!/usr/bin/env python3
"""Pymodbus asynchronous Server Example.

An example of a multi threaded asynchronous server.

usage: server_async.py [-h] [--comm {tcp,udp,serial,tls}]
                       [--framer {ascii,binary,rtu,socket,tls}]
                       [--log {critical,error,warning,info,debug}]
                       [--port PORT] [--store {sequential,sparse,factory,none}]
                       [--slaves SLAVES]

Command line options for examples

options:
  -h, --help            show this help message and exit
  --comm {tcp,udp,serial,tls}
                        "serial", "tcp", "udp" or "tls"
  --framer {ascii,binary,rtu,socket,tls}
                        "ascii", "binary", "rtu", "socket" or "tls"
  --log {critical,error,warning,info,debug}
                        "critical", "error", "warning", "info" or "debug"
  --port PORT           the port to use
  --store {sequential,sparse,factory,none}
                        "sequential", "sparse", "factory" or "none"
  --slaves SLAVES       number of slaves to respond to

The corresponding client can be started as:
    python3 client_sync.py
"""
import asyncio
import logging

from examples.helper import get_commandline
from examples.server_async import run_async_server, setup_server
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)


_logger = logging.getLogger()


async def updating_task(context):
    """Run every so often,

    and updates live values of the context. It should be noted
    that there is a lrace condition for the update.
    """
    _logger.debug("updating the context")
    fc_as_hex = 3
    slave_id = 0x00
    address = 0x10
    values = context[slave_id].getValues(fc_as_hex, address, count=5)
    values = [v + 1 for v in values]  # increment by 1.
    txt = f"new values: {str(values)}"
    _logger.debug(txt)
    context[slave_id].setValues(fc_as_hex, address, values)
    await asyncio.sleep(1)


def setup_updating_server(args):
    """Run server setup."""
    # The datastores only respond to the addresses that are initialized
    # If you initialize a DataBlock to addresses of 0x00 to 0xFF, a request to
    # 0x100 will respond with an invalid address exception.
    # This is because many devices exhibit this kind of behavior (but not all)

    # Continuing, use a sequential block without gaps.
    datablock = ModbusSequentialDataBlock(0x00, [17] * 100)
    context = ModbusSlaveContext(
        di=datablock, co=datablock, hr=datablock, ir=datablock, unit=1
    )
    args.context = ModbusServerContext(slaves=context, single=True)
    return setup_server(args)


async def run_updating_server(args):
    """Start updater task and async server."""
    asyncio.create_task(updating_task(args.context))
    await run_async_server(args)


if __name__ == "__main__":
    cmd_args = get_commandline(
        server=True,
        description="Run asynchronous server.",
    )
    run_args = setup_updating_server(cmd_args)
    asyncio.run(run_updating_server(run_args), debug=True)
