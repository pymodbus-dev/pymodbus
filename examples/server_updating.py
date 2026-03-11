#!/usr/bin/env python3
"""Pymodbus asynchronous Server with updating task Example.

An example of an asynchronous server and
a task that runs continuously alongside the server and updates values.

A real world example controlling a heatpump can be found at

    examples/heatpump.py

usage::

    server_updating.py [-h]
                       [--log {critical,error,warning,info,debug}]
                       [--port PORT]
                       [--baudrate BAUDRATE]
                       [--host HOST]

    -h, --help
        show this help message and exit
    -l, --log {critical,error,warning,info,debug}
        set log level, default is info
    -p, --port PORT
        set port
    --baudrate BAUDRATE
        set serial device baud rate
    --host HOST
        set HOST

The corresponding client can be started as:
    python3 client_sync.py
"""
import argparse
import asyncio
import logging

from pymodbus import pymodbus_apply_logging_config
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice


_logger = logging.getLogger(__name__)

def get_commandline(cmdline: list[str] | None = None):
    """Read and check command line arguments."""
    parser = argparse.ArgumentParser(description="server_update")
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
        "--host",
        help="set host, default is 127.0.0.1",
        dest="host",
        default=None,
        type=str,
    )
    args = parser.parse_args(cmdline)
    pymodbus_apply_logging_config(args.log.upper())
    _logger.setLevel(args.log.upper())
    args.port = args.port or 5020
    return args



async def updating_task(server):
    """Update values in server.

    This task runs continuously beside the server
    It will increment some values each two seconds.

    It should be noted that async_getValues and async_setValues are not safe
    against concurrent use.
    """
    func_code = 3
    device_id = 0x01
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
    args = get_commandline(cmdline=cmdline)
    server = ModbusTcpServer(
        SimDevice(1, SimData(0, datatype=DataType.REGISTERS, values=[17]*100)),
        address=(args.host if args.host else "", args.port if args.port else 0)
    )
    return server


async def run_updating_server(server):
    """Start updating_task concurrently with the current task."""
    task = asyncio.create_task(updating_task(server))
    task.set_name("example updating task")
    await server.serve_forever()  # start the server
    task.cancel()


async def main(cmdline=None):
    """Combine setup and run."""
    server = setup_updating_server(cmdline=cmdline)
    await run_updating_server(server)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
