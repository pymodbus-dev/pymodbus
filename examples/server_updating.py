#!/usr/bin/env python3
"""Pymodbus asynchronous Server with updating task Example.

An example of an asynchronous server and
a task that runs continuously alongside the server and updates values.

usage::

    server_updating.py [-h] [--comm {tcp,udp,serial,tls}]
                       [--framer {ascii,rtu,socket,tls}]
                       [--log {critical,error,warning,info,debug}]
                       [--port PORT] [--store {sequential,sparse,factory,none}]
                       [--slaves SLAVES]

    -h, --help
        show this help message and exit
    -c, --comm {tcp,udp,serial,tls}
        set communication, default is tcp
    -f, --framer {ascii,rtu,socket,tls}
        set framer, default depends on --comm
    -l, --log {critical,error,warning,info,debug}
        set log level, default is info
    -p, --port PORT
        set port
        set serial device baud rate
    --store {sequential,sparse,factory,none}
        set datastore type
    --slaves SLAVES
        set number of slaves to respond to

The corresponding client can be started as:
    python3 client_sync.py
"""
import asyncio
import logging

import server_async

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)


_logger = logging.getLogger(__name__)


async def updating_task(context):
    """Update values in server.

    This task runs continuously beside the server
    It will increment some values each two seconds.

    It should be noted that getValues and setValues are not safe
    against concurrent use.
    """
    fc_as_hex = 3
    slave_id = 0x00
    address = 0x10
    count = 6

    # set values to zero
    values = await context[slave_id].async_getValues(fc_as_hex, address, count=count)
    values = [0 for v in values]
    await context[slave_id].async_setValues(fc_as_hex, address, values)

    txt = (
        f"updating_task: started: initialised values: {values!s} at address {address!s}"
    )
    print(txt)
    _logger.debug(txt)

    # incrementing loop
    while True:
        await asyncio.sleep(2)

        values = await context[slave_id].async_getValues(
            fc_as_hex, address, count=count
        )
        values = [v + 1 for v in values]
        await context[slave_id].async_setValues(fc_as_hex, address, values)

        txt = f"updating_task: incremented values: {values!s} at address {address!s}"
        print(txt)
        _logger.debug(txt)


def setup_updating_server(cmdline=None):
    """Run server setup."""
    # The datastores only respond to the addresses that are initialized
    # If you initialize a DataBlock to addresses of 0x00 to 0xFF, a request to
    # 0x100 will respond with an invalid address exception.
    # This is because many devices exhibit this kind of behavior (but not all)

    # Continuing, use a sequential block without gaps.
    datablock = ModbusSequentialDataBlock(0x00, [17] * 100)
    context = ModbusSlaveContext(di=datablock, co=datablock, hr=datablock, ir=datablock)
    context = ModbusServerContext(slaves=context, single=True)
    return server_async.setup_server(
        description="Run asynchronous server.", context=context, cmdline=cmdline
    )


async def run_updating_server(args):
    """Start updating_task concurrently with the current task."""
    task = asyncio.create_task(updating_task(args.context))
    task.set_name("example updating task")
    await server_async.run_async_server(args)  # start the server
    task.cancel()


async def main(cmdline=None):
    """Combine setup and run."""
    run_args = setup_updating_server(cmdline=cmdline)
    await run_updating_server(run_args)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
