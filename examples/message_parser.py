#!/usr/bin/env python3
"""Modbus Message Parser.

The following is an example of how to parse modbus messages
using the supplied framers.

"""
import argparse
import codecs as c
import collections
import logging
import textwrap

from pymodbus import pymodbus_apply_logging_config
from pymodbus.framer import (
    FramerAscii,
    FramerRTU,
    FramerSocket,
)
from pymodbus.pdu import DecodePDU


_logger = logging.getLogger(__file__)


def get_commandline(cmdline):
    """Parse the command line options."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--framer",
        choices=["ascii", "rtu", "socket"],
        help="set framer, default is rtu",
        type=str,
        default="rtu",
        dest="framer",
    )
    parser.add_argument(
        "-l",
        "--log",
        choices=["critical", "error", "warning", "info", "debug"],
        help="set log level, default is info",
        default="info",
        type=str,
        dest="log",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="The message to parse",
        type=str,
        default=None,
        dest="message",
    )
    return parser.parse_args(cmdline)


class Decoder:
    """Decoder.

    build custom wrapper around the framers
    """

    def __init__(self, framer, encode=False):
        """Initialize a new instance of the decoder."""
        self.framer = framer
        self.encode = encode

    def decode(self, message):
        """Attempt to decode the supplied message."""
        value = message if self.encode else c.encode(message, "hex_codec")
        print("=" * 80)
        print(f"Decoding Message {value!r}")
        print("=" * 80)
        decoders = [
            self.framer(DecodePDU(True)),
            self.framer(DecodePDU(False)),
        ]
        for decoder in decoders:
            print(f"{decoder.decoder.__class__.__name__}")
            print("-" * 80)
            try:
                _, pdu = decoder.handleFrame(message, 0, 0)
                self.report(pdu)
            except Exception:  # pylint: disable=broad-except
                self.check_errors(decoder, message)

    def check_errors(self, decoder, message):
        """Attempt to find message errors."""
        txt = f"Unable to parse message - {message} with {decoder}"
        _logger.error(txt)

    def report(self, message):
        """Print the message information."""
        print(
            f"{'name':.15s} = {message.__class__.__name__}"
        )
        for k_dict, v_dict in message.__dict__.items():
            if isinstance(v_dict, dict):  # pragma: no cover
                print(f"{k_dict:.15s} =")
                for k_item, v_item in v_dict.items():
                    print(f"  {k_item:.12s} => {v_item}"
                    )
            elif isinstance(v_dict, collections.abc.Iterable):
                print(f"{k_dict:.15s} =")
                value = str([int(x) for x in v_dict])
                for line in textwrap.wrap(value, 60):
                    print(f"{' ':.15s} . {line}")
            else:
                print(f"{k_dict:.15s} = {hex(v_dict)}")
        print("{'documentation':.15s} = {message.__doc__}")


# -------------------------------------------------------------------------- #
# and decode our message
# -------------------------------------------------------------------------- #


def parse_messages(cmdline=None):
    """Do a helper method to generate the messages to parse."""
    args = get_commandline(cmdline=cmdline)
    pymodbus_apply_logging_config(args.log.upper())
    _logger.setLevel(args.log.upper())
    if not args.message:  # pragma: no cover
        _logger.error("Missing --message.")
        return

    framer = {
        "ascii": FramerAscii,
        "rtu": FramerRTU,
        "socket": FramerSocket,
    }[args.framer]
    decoder = Decoder(framer)

    raw_message = c.decode(args.message.encode(), "hex_codec")
    decoder.decode(raw_message)


def main(cmdline=None):
    """Run program."""
    parse_messages(cmdline=cmdline)


if __name__ == "__main__":
    main()
