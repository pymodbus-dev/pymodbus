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

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
)


_logger = logging.getLogger()


def get_commandline(cmdline):
    """Parse the command line options"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--framer",
        choices=["ascii", "binary", "rtu", "socket"],
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
        """Initialize a new instance of the decoder"""
        self.framer = framer
        self.encode = encode

    def decode(self, message):
        """Attempt to decode the supplied message"""
        value = message if self.encode else c.encode(message, "hex_codec")
        print("=" * 80)
        print(f"Decoding Message {value}")
        print("=" * 80)
        decoders = [
            self.framer(ServerDecoder(), client=None),
            self.framer(ClientDecoder(), client=None),
        ]
        for decoder in decoders:
            print(f"{decoder.decoder.__class__.__name__}")
            print("-" * 80)
            try:
                decoder.addToFrame(message)
                if decoder.checkFrame():
                    slave = decoder._header.get(  # pylint: disable=protected-access
                        "uid", 0x00
                    )
                    decoder.advanceFrame()
                    decoder.processIncomingPacket(message, self.report, slave)
                else:
                    self.check_errors(decoder, message)
            except Exception:  # pylint: disable=broad-except
                self.check_errors(decoder, message)

    def check_errors(self, decoder, message):
        """Attempt to find message errors"""
        txt = f"Unable to parse message - {message} with {decoder}"
        _logger.error(txt)

    def report(self, message):
        """Print the message information"""
        print(
            "%-15s = %s"  # pylint: disable=consider-using-f-string
            % (
                "name",
                message.__class__.__name__,
            )
        )
        for k_dict, v_dict in message.__dict__.items():
            if isinstance(v_dict, dict):
                print("%-15s =" % k_dict)  # pylint: disable=consider-using-f-string
                for k_item, v_item in v_dict.items():
                    print(
                        "  %-12s => %s"  # pylint: disable=consider-using-f-string
                        % (k_item, v_item)
                    )
            elif isinstance(v_dict, collections.abc.Iterable):
                print("%-15s =" % k_dict)  # pylint: disable=consider-using-f-string
                value = str([int(x) for x in v_dict])
                for line in textwrap.wrap(value, 60):
                    print(
                        "%-15s . %s"  # pylint: disable=consider-using-f-string
                        % ("", line)
                    )
            else:
                print(
                    "%-15s = %s"  # pylint: disable=consider-using-f-string
                    % (k_dict, hex(v_dict))
                )
        print(
            "%-15s = %s"  # pylint: disable=consider-using-f-string
            % (
                "documentation",
                message.__doc__,
            )
        )


# -------------------------------------------------------------------------- #
# and decode our message
# -------------------------------------------------------------------------- #


def parse_messages(cmdline=None):
    """Do a helper method to generate the messages to parse"""
    args = get_commandline(cmdline=cmdline)
    _logger.setLevel(args.log.upper())
    if not args.message:
        _logger.error("Missing --message.")
        return

    framer = {
        "ascii": ModbusAsciiFramer,
        "binary": ModbusBinaryFramer,
        "rtu": ModbusRtuFramer,
        "socket": ModbusSocketFramer,
    }[args.framer]
    decoder = Decoder(framer)

    raw_message = c.decode(args.message.encode(), "hex_codec")
    decoder.decode(raw_message)


if __name__ == "__main__":
    parse_messages()
