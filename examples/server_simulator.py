#!/usr/bin/env python3
"""Pymodbus Simulator Example.

An example of using simulator datastore with json interface.

usage: server_simulator.py [-h]
                       [--log {critical,error,warning,info,debug}]
                       [--port PORT]

Command line options for examples

options:
  -h, --help            show this help message and exit
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

demo_config = {
    "setup": {
        "co size": 100,
        "di size": 150,
        "hr size": 200,
        "ir size": 250,
        "shared blocks": True,
        "type exception": False,
        "defaults": {
            "value": {
                "bits": 0x0708,
                "uint16": 1,
                "uint32": 45000,
                "float32": 127.4,
                "string": "X",
            },
            "action": {
                "bits": None,
                "uint16": None,
                "uint32": None,
                "float32": None,
                "string": None,
            },
        },
    },
    "invalid": [
        1,
        [3, 4],
    ],
    "write": [
        5,
        [7, 8],
        [16, 18],
        [21, 26],
        [31, 36],
    ],
    "bits": [
        5,
        [7, 8],
        {"addr": 10, "value": 0x81},
        {"addr": [11, 12], "value": 0x04342},
        {"addr": 13, "action": "reset"},
        {"addr": 14, "value": 15, "action": "reset"},
    ],
    "uint16": [
        {"addr": 16, "value": 3124},
        {"addr": [17, 18], "value": 5678},
        {"addr": [19, 20], "value": 14661, "action": "increment"},
    ],
    "uint32": [
        {"addr": [21, 22], "value": 3124},
        {"addr": [23, 26], "value": 5678},
        {"addr": [27, 30], "value": 345000, "action": "increment"},
    ],
    "float32": [
        {"addr": [31, 32], "value": 3124.17},
        {"addr": [33, 36], "value": 5678.19},
        {"addr": [37, 40], "value": 345000.18, "action": "increment"},
    ],
    "string": [
        {"addr": [41, 42], "value": "Str"},
        {"addr": [43, 44], "value": "Strx"},
    ],
    "repeat": [{"addr": [0, 45], "to": [46, 138]}],
}


def custom_action1(_inx, _cell):
    """Test action."""


def custom_action2(_inx, _cell):
    """Test action."""


demo_actions = {
    "custom1": custom_action1,
    "custom2": custom_action2,
}


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
    parser.add_argument("--port", help="set port", type=str, default="5020")
    args = parser.parse_args()

    pymodbus_apply_logging_config()
    _logger.setLevel(args.log.upper())
    args.framer = ModbusSocketFramer
    args.port = int(args.port)
    return args


def setup_simulator(args, setup=None, actions=None):
    """Run server setup."""
    _logger.info("### Create datastore")
    if not setup:
        setup = demo_config
    if not actions:
        actions = demo_actions
    context = ModbusSimulatorContext(setup, actions)
    args.context = ModbusServerContext(slaves=context, single=True)
    return args


async def run_server_simulator(args):
    """Run server."""
    _logger.info("### start server simulator")
    await StartAsyncTcpServer(
        context=args.context,
        address=("", args.port),
        framer=args.framer,
        allow_reuse_address=True,
    )


if __name__ == "__main__":
    cmd_args = get_commandline()
    run_args = setup_simulator(cmd_args)
    asyncio.run(run_server_simulator(run_args), debug=True)
