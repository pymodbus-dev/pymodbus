"""Pymodbus asynchronous Server with updating subroutine Example.

An example of an asynchronous server with multiple threads and
a subroutine that runs continuously alongside the server and updates values.

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

from examples.server_async import run_async_server, setup_server
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)


_logger = logging.getLogger(__name__)


async def updating_task(context):
    """
    This subroutine will run continously beside the server and
    increment each two seconds some values (via asyncio.create_task
    in run_updating_server).

    It should be noted that getValues and setValues are not thread safe.
    """

    fc_as_hex = 3
    slave_id = 0x00
    address = 7
    
    # set values to zero
    values = context[slave_id].getValues(fc_as_hex, address, count=6)
    values = [0 for v in values]
    context[slave_id].setValues(fc_as_hex, address, values)

    txt = f"updating_task: started: initialised values: {values!s} at address {address!s}"
    print(txt)
    _logger.debug(txt)

    # incrementing loop 
    while True:
        await asyncio.sleep(5)
        
        values = context[slave_id].getValues(fc_as_hex, address, count=6)
        values = [v + 1 for v in values] 
        context[slave_id].setValues(fc_as_hex, address, values)

        txt = f"updating_task: incemented values: {values!s} at address {address!s}"
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
    return setup_server(
        description="Run asynchronous server.", context=context, cmdline=cmdline
    )


async def run_updating_server(args):
    """Start updater task and async server."""
    asyncio.create_task(updating_task(args.context)) # start updating_task concurrently with the current task
    await run_async_server(args) # start the server


async def main(cmdline=None):
    """Combine setup and run"""
    run_args = setup_updating_server(cmdline=cmdline)
    await run_updating_server(run_args)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)  # pragma: no cover
