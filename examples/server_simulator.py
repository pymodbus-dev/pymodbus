#!/usr/bin/env python3
"""Pymodbus Simulator Example.

An example of using simulator datastore with json interface.

usage: server_simulator.py [-h] [--path JSON_FILE]
                       [--log {critical,error,warning,info,debug}]
                       [--port PORT]

Command line options for examples

options:
  -h, --help            show this help message and exit
  --path JSON_FILE      path to json device configuration file
  --log {critical,error,warning,info,debug}
                        "critical", "error", "warning", "info" or "debug"
  --port PORT           the port to use

The corresponding client can be started as:
    python3 client_sync.py
"""
import argparse
import asyncio
import logging

from pymodbus import pymodbus_apply_logging_config
from pymodbus.datastore import ModbusServerContext, ModbusSimulatorContext
from pymodbus.server import StartAsyncTcpServer
from pymodbus.transaction import ModbusSocketFramer


_logger = logging.getLogger()


def get_commandline():
    """Read and validate command line arguments"""
    parser = argparse.ArgumentParser(description="Run server simulator.")
    parser.add_argument(
        "--log",
        choices=["critical", "error", "warning", "info", "debug"],
        help="set log level, default is info",
        default="info",
        type=str,
    )
    parser.add_argument(
        "--port",
        help="set port",
        type=str,
    )
    parser.add_argument(
        "--json",
        help="path to json device configuration file",
        default=None,
        type=str,
    )
    args = parser.parse_args()

    pymodbus_apply_logging_config()
    _logger.setLevel(args.log.upper())
    args.framer = ModbusSocketFramer
    args.port = int(args.port) or 5020
    return args


def setup_server(args, json_dict=None):
    """Run server setup."""
    _logger.info("### Create datastore")
    context = ModbusSimulatorContext()

    if args.path:
        context.load_file(args.path, None)
    else:
        context.load_dict(json_dict, None)
    args.context = ModbusServerContext(slaves=context, single=True)
    return args


async def run_server_simulator(args):
    """Run server."""
    _logger.info("### start server simulator")
    await StartAsyncTcpServer(
        context=args.context,
        address=("", args.port) if args.port else None,
        framer=args.framer,  # The framer strategy to use
        allow_reuse_address=True,  # allow the reuse of an address
    )


if __name__ == "__main__":
    cmd_args = get_commandline()
    run_args = setup_server(cmd_args)
    asyncio.run(run_server_simulator(run_args), debug=True)
