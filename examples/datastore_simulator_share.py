#!/usr/bin/env python3
"""Pymodbus datastore simulator Example.

An example of using simulator datastore with json interface.

Detailed description of the device definition can be found at:

    https://pymodbus.readthedocs.io/en/latest/source/library/simulator/config.html#device-entries

usage::

    datastore_simulator_share.py [-h]
                        [--log {critical,error,warning,info,debug}]
                        [--port PORT]
                        [--test_client]

    -h, --help
        show this help message and exit
    -l, --log {critical,error,warning,info,debug}
        set log level
    -p, --port PORT
        set port to use
    --test_client
        starts a client to test the configuration

The corresponding client can be started as:
    python3 client_sync.py

.. tip:: This is NOT the pymodbus simulator, that is started as pymodbus.simulator.
"""
import argparse
import asyncio
import logging

from pymodbus import pymodbus_apply_logging_config
from pymodbus.datastore import ModbusServerContext, ModbusSimulatorContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import StartAsyncTcpServer


_logger = logging.getLogger(__file__)

demo_config = {
        "setup": {
            "co size": 100,
            "di size": 150,
            "hr size": 200,
            "ir size": 300,
            "shared blocks": True,
            "type exception": False,
            "defaults": {
                "value": {
                    "bitfield16": 0x0708,
                    "bitfield32": 0x10010708,
                    "bitfield64": 0x8001000000003708,
                    "int16": -1,
                    "int32": -45000,
                    "int64": -450000000,
                    "uint16": 1,
                    "uint32": 45000,
                    "uint64": 450000000,
                    "float32": 127.4,
                    "float64": 10127.4,
                    "string": "X",
                },
                "action": {
                    "bitfield16": None,
                    "bitfield32": None,
                    "bitfield64": None,
                    "int16": None,
                    "int32": None,
                    "int64": None,
                    "uint16": None,
                    "uint32": None,
                    "uint64": None,
                    "float32": None,
                    "float64": None,
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
            [33, 38],
        ],
        "bitfield16": [
            [7, 7],
            [8, 8],
            {"addr": 2, "value": 0x81},
            {"addr": 3, "value": 17},
            {"addr": 4, "value": 17},
            {"addr": 5, "value": 17},
            {"addr": 10, "value": 0x81},
            {"addr": [11, 11], "value": 0x04342},
            {"addr": [12, 12], "value": 0x04342},
            {"addr": 13, "action": "random"},
            {"addr": 14, "value": 15, "action": "reset"},
        ],
        "bitfield32": [
            [50, 51],
            {"addr": [52,53], "value": 0x04342},
        ],
        "bitfield64": [
            [54, 57],
            {"addr": [58,61], "value": 0x04342},
        ],
        "int16": [
            70,
            [71, 71],
            {"addr": 72, "value": 0x81},
            {"addr": [73, 73], "value": 0x04342},
            {"addr": 74, "action": "random"},
            {"addr": 75, "value": 15, "action": "reset"},
        ],
        "int32": [
            [76, 77],
            {"addr": [78,79], "value": 0x04342},
        ],
        "int64": [
            [80, 83],
            {"addr": [84,87], "value": 0x04342},
        ],
        "uint16": [
            {"addr": 16, "value": 3124},
            {"addr": [17, 18], "value": 5678},
            {
                "addr": [19, 20],
                "value": 14661,
                "action": "increment",
                "args": {"minval": 1, "maxval": 100},
            },
        ],
        "uint32": [
            {"addr": [21, 22], "value": 3124},
            {"addr": [23, 26], "value": 5678},
            {"addr": [27, 30], "value": 345000, "action": "increment"},
            {
                "addr": [31, 32],
                "value": 50,
                "action": "random",
                "kwargs": {"minval": 10, "maxval": 80},
            },
        ],
        "uint64": [
            {"addr": [62, 65], "value": 3124}
        ],
        "float32": [
            {"addr": [33, 34], "value": 3124.5},
            {"addr": [35, 38], "value": 5678.19},
            {"addr": [39, 42], "value": 345000.18, "action": "increment"},
        ],
        "float64": [
            {"addr": [66, 69], "value": 3124.5},
        ],
        "string": [
            {"addr": [43, 44], "value": "Str"},
            {"addr": [45, 48], "value": "Strxyz12"},
        ],
        "repeat": [{"addr": [0, 95], "to": [96, 191]},
                   {"addr": [0, 95], "to": [192, 287]}],
    }

def custom_action1(_inx, _cell):
    """Test action."""


def custom_action2(_inx, _cell):
    """Test action."""


demo_actions = {
    "custom1": custom_action1,
    "custom2": custom_action2,
}


def get_commandline(cmdline=None):
    """Read and validate command line arguments."""
    parser = argparse.ArgumentParser(description="Run datastore simulator example.")
    parser.add_argument(
        "--log",
        choices=["critical", "error", "warning", "info", "debug"],
        help="set log level, default is info",
        default="info",
        type=str,
    )
    parser.add_argument("--port", help="set port", type=str, default="5020")
    parser.add_argument("--host", help="set interface", type=str, default="localhost")
    parser.add_argument("--test_client", help="start client to test", action="store_true")
    args = parser.parse_args(cmdline)
    return args


def setup_simulator(setup=None, actions=None, cmdline=None):
    """Run server setup."""
    if not setup:
        setup=demo_config
    if not actions:
        actions=demo_actions
    args = get_commandline(cmdline=cmdline)
    pymodbus_apply_logging_config(args.log.upper())
    _logger.setLevel(args.log.upper())
    args.port = int(args.port)

    context = ModbusSimulatorContext(setup, actions)
    args.context = ModbusServerContext(slaves=context, single=True)
    args.identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "Pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/pymodbus-dev/pymodbus/",
            "ProductName": "Pymodbus Server",
            "ModelName": "Pymodbus Server",
            "MajorMinorRevision": "test",
        }
    )
    return args


async def run_server_simulator(args):
    """Run server."""
    _logger.info("### start server simulator")

    await StartAsyncTcpServer(
        context=args.context,
        address=(args.host, args.port),
    )


async def main(cmdline=None):
    """Combine setup and run."""
    run_args = setup_simulator(cmdline=cmdline)
    await run_server_simulator(run_args)


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
