"""Helper for examples.

Contains common functions get get_command_line() to avoid duplicating
code that are not relevant for the examples as such, like e.g.
get_command_line
"""
import argparse
import logging

from pymodbus import pymodbus_apply_logging_config
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)


_logger = logging.getLogger()


def get_commandline(server=False, description=None, extras=None):
    """Read and validate command line arguments"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--comm",
        choices=["tcp", "udp", "serial", "tls"],
        help="set communication, default is tcp",
        default="tcp",
        type=str,
    )
    parser.add_argument(
        "--framer",
        choices=["ascii", "binary", "rtu", "socket", "tls"],
        help="set framer, default depends on --comm",
        type=str,
    )
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
    if server:
        parser.add_argument(
            "--store",
            choices=["sequential", "sparse", "factory", "none"],
            help="set type of datastore",
            default="sequential",
            type=str,
        )
        parser.add_argument(
            "--slaves",
            help="set number of slaves, default is 0 (any)",
            default=0,
            type=int,
            nargs="+",
        )
    if extras:
        for extra in extras:
            parser.add_argument(extra[0], **extra[1])
    args = parser.parse_args()

    # set defaults
    comm_defaults = {
        "tcp": ["socket", 5020],
        "udp": ["socket", 5020],
        "serial": ["rtu", "/dev/ptyp0"],
        "tls": ["tls", 5020],
    }
    framers = {
        "ascii": ModbusAsciiFramer,
        "binary": ModbusBinaryFramer,
        "rtu": ModbusRtuFramer,
        "socket": ModbusSocketFramer,
        "tls": ModbusTlsFramer,
    }
    pymodbus_apply_logging_config()
    _logger.setLevel(args.log.upper())
    args.framer = framers[args.framer or comm_defaults[args.comm][0]]
    args.port = args.port or comm_defaults[args.comm][1]
    if args.comm != "serial" and args.port:
        args.port = int(args.port)
    return args
