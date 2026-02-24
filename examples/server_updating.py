#!/usr/bin/env python3
"""Pymodbus asynchronous Server with updating task Example.

An example of an asynchronous server and
a task that runs continuously alongside the server and updates values.

usage::

    server_updating.py [-h]
                       [--port PORT]
                       [--host HOST]

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
    --host HOST
        set HOST

The corresponding client can be started as:
    python3 client_sync.py
"""
import asyncio
import logging
import argparse


from pymodbus.simulator import DataType, SimData, SimDevice
from pymodbus import pymodbus_apply_logging_config

_logger = logging.getLogger(__name__)

def get_commandline(server: bool = False, description: str | None = None, extras: Any = None, cmdline: list[str] | None = None):
    """Read and check command line arguments."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-c",
        "--comm",
        choices=["tcp", "udp", "serial", "tls", "unknown"],
        help="set communication, default is tcp",
        dest="comm",
        default="tcp",
        type=str,
    )
    parser.add_argument(
        "-f",
        "--framer",
        choices=["ascii", "rtu", "socket", "tls"],
        help="set framer, default depends on --comm",
        dest="framer",
        type=str,
    )
    parser.add_argument(
        "-l",
        "--log",
        choices=["critical", "error", "warning", "info", "debug"],
        help="set log level, default is info",
        dest="log",
        default="info",
        type=str,
    )
    parser.add_argument(
        "-p",
        "--port",
        help="set port",
        dest="port",
        type=str,
    )
    parser.add_argument(
        "--baudrate",
        help="set serial device baud rate",
        default=9600,
        type=int,
    )
    parser.add_argument(
        "--host",
        help="set host, default is 127.0.0.1",
        dest="host",
        default=None,
        type=str,
    )
    if server:
        parser.add_argument(
            "--device_ids",
            help="set number of device_ids, default is 0 (any)",
            default=0,
            type=int,
        )
        parser.add_argument(
            "--context",
            help="ADVANCED USAGE: set datastore context object",
            default=None,
        )
    else:
        parser.add_argument(
            "--timeout",
            help="ADVANCED USAGE: set client timeout",
            default=10,
            type=float,
        )
    if extras:  # pragma: no cover
        for extra in extras:
            parser.add_argument(extra[0], **extra[1])
    args = parser.parse_args(cmdline)

    # set defaults
    comm_defaults: dict[str, list[int | str]] = {
        "tcp": ["socket", 5020],
        "udp": ["socket", 5020],
        "serial": ["rtu", "/dev/ptyp0"],
        "tls": ["tls", 5020],
    }
    pymodbus_apply_logging_config(args.log.upper())
    _logger.setLevel(args.log.upper())
    if not args.framer:
        args.framer = comm_defaults[args.comm][0]
    args.port = args.port or comm_defaults[args.comm][1]
    if args.comm != "serial" and args.port:
        args.port = int(args.port)
    if not args.host:
        args.host = "" if server else "127.0.0.1"
    return args



async def updating_task(server):
    """Update values in server.

    This task runs continuously beside the server
    It will increment some values each two seconds.

    It should be noted that async_getValues and async_setValues are not safe
    against concurrent use.
    """
    func_code = 3
    device_id = 0x00
    address = 0x10
    count = 6

    # set values to zero
    values = await server.async_getValues(device_id, func_code, address, count=count)
    values = [0 for v in values]
    await server.async_setValues(device_id, func_code, address, values)

    txt = (
        f"updating_task: started: initialised values: {values!s} at address {address!s}"
    )
    print(txt)
    _logger.debug(txt)

    # incrementing loop
    while True:
        await asyncio.sleep(2)

        values = await server.async_getValues(device_id, func_code, address, count=count)
        values = [v + 1 for v in values]
        await server.async_setValues(device_id, func_code, address, values)

        txt = f"updating_task: incremented values: {values!s} at address {address!s}"
        print(txt)
        _logger.debug(txt)


def setup_updating_server(cmdline=None):
    """Run server setup."""
    # The datastores only respond to the addresses that are initialized
    # If you initialize a DataBlock to addresses of 0x00 to 0xFF, a request to
    # 0x100 will respond with an invalid address exception.
    # This is because many devices exhibit this kind of behavior (but not all)
    context = SimDevice(0, SimData(0, datatype=DataType.REGISTERS, values=[17]*100))
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
