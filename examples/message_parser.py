#!/usr/bin/env python3
"""Modbus Message Parser.

The following is an example of how to parse modbus messages
using the supplied framers for a number of protocols:

* tcp
* ascii
* rtu
* binary
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


class Decoder:
    """Decoder.

    build a quick wrapper around the framers
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
        for (k_dict, v_dict) in message.__dict__.items():
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
def get_options(cmdline):
    """Parse the command line options"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--framer",
        choices=["ascii", "binary", "rtu", "socket", "tls"],
        help="set framer, default depends on --comm",
        type=str,
        default="rtu",
        dest="framer",
    )
    parser.add_argument(
        "--log",
        choices=["critical", "error", "warning", "info", "debug"],
        help="set log level, default is info",
        default="info",
        type=str,
        dest="log",
    )
    parser.add_argument(
        "--message", help="The message to parse", default=None, type=str, dest="message"
    )
    parser.add_argument(
        "--file",
        help="The file containing messages to parse",
        default=None,
        type=str,
        dest="file",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["ascii", "binary", "hex"],
        help="message/file format",
        dest="type",
        default="hex",
    )
    return parser.parse_args(cmdline)


def get_messages(option):
    """Do a helper method to generate the messages to parse"""
    if option.message:
        if option.transaction:
            msg = ""
            for segment in option.message.split():
                segment = segment.replace("0x", "")
                segment = "0" + segment if len(segment) == 1 else segment
                msg = msg + segment
            option.message = msg

        if option.type != "ascii":
            option.message = c.decode(option.message.encode(), "hex_codec")
        yield option.message
    elif option.file:
        with open(option.file, "r") as handle:  # pylint: disable=unspecified-encoding
            for line in handle:
                if line.startswith("#"):
                    continue
                if option.type != "ascii":
                    line = line.strip()
                    line = line.decode("hex")
                yield line


def main(cmdline=None):
    """Run main runner function"""
    option = get_options(cmdline)
    _logger.setLevel(option.log.upper())

    framer = {
        "tcp": ModbusSocketFramer,
        "rtu": ModbusRtuFramer,
        "binary": ModbusBinaryFramer,
        "ascii": ModbusAsciiFramer,
    }.get(option.framer, ModbusSocketFramer)

    decoder = Decoder(framer)
    for message in get_messages(option):
        decoder.decode(message)


if __name__ == "__main__":
    main()
