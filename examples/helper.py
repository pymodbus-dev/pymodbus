"""Pymodbus common helper functions for all examples

A set of helper methods and constants, instead of maintaining these
in each example.
"""
import argparse
import logging
import sys

# --------------------------------------------------------------------------- #
# configure logging
# --------------------------------------------------------------------------- #
FORMAT = (
    "%(asctime)-15s %(threadName)-15s "
    "%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)
_logger = logging.getLogger()


def get_commandline(is_server):
    """Read and validate command line arguments"""
    parser = argparse.ArgumentParser(description="Command line options for examples")
    parser.add_argument(
        "--comm",
        choices=["tcp", "udp", "serial", "tls"],
        help='"serial", "tcp", "udp" or "tls"'
    )
    parser.add_argument(
        "--framer",
        choices=["ascii", "binary", "rtu", "socket", "tls"],
        help='"ascii", "binary", "rtu", "socket" or "tls"'
    )
    parser.add_argument(
        "--log",
        choices=["critical", "error", "warning", "info", "debug"],
        help='"critical", "error", "warning", "info" or "debug"'
    )
    if is_server:
        parser.add_argument(
            "--store",
            choices=["sequential", "sparse", "factory", "none"],
            help='"sequential", "sparse", "factory" or "none"'
        )
        parser.add_argument(
            "--slaves",
            type=int,
            help='number of slaves to respond to'
        )
    args = parser.parse_args()

    # set defaults
    if args.log:
        _logger.setLevel(args.log.upper())
    else:
        _logger.setLevel(logging.INFO)
    if not args.comm:
        args.comm = "tcp"
    return args


if __name__ == "__main__":
    _logger.error("helper.py cannot be run standalone!")
    sys.exit(-1)
