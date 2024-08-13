"""Helper for commandline etc.

Contains common functions get get_command_line() to avoid duplicating
code that are not relevant for the code as such, like e.g.
get_command_line
"""
import argparse
import logging
import os

from pymodbus import pymodbus_apply_logging_config


_logger = logging.getLogger(__file__)


def get_commandline(server=False, description=None, extras=None, cmdline=None):
    """Read and validate command line arguments."""
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
    if extras:
        for extra in extras:
            parser.add_argument(extra[0], **extra[1])
    args = parser.parse_args(cmdline)

    # set defaults
    comm_defaults = {
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


def get_certificate(suffix: str):
    """Get example certificate."""
    delimiter = "\\" if os.name == "nt" else "/"
    cwd = os.getcwd().split(delimiter)[-1]
    if cwd == "examples":
        path = "."
    elif cwd == "sub_examples":
        path = "../../examples"
    elif cwd == "test":
        path = "../examples"
    elif cwd == "pymodbus":
        path = "examples"
    else:
        raise RuntimeError(f"**Error** Cannot find certificate path={cwd}")
    return f"{path}/certificates/pymodbus.{suffix}"
