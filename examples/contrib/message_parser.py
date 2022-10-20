#!/usr/bin/env python3
# pylint: disable=missing-type-doc,missing-param-doc,differing-param-doc,missing-any-param-doc
"""Modbus Message Parser.

The following is an example of how to parse modbus messages
using the supplied framers for a number of protocols:

* tcp
* ascii
* rtu
* binary
"""
# -------------------------------------------------------------------------- #
# import needed libraries
# -------------------------------------------------------------------------- #

import codecs as c
import collections
import logging
import textwrap
from optparse import OptionParser  # pylint: disable=deprecated-module

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
)


# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
FORMAT = (
    "%(asctime)-15s %(threadName)-15s"
    " %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s"
)
logging.basicConfig(format=FORMAT)
log = logging.getLogger()


# -------------------------------------------------------------------------- #
# build a quick wrapper around the framers
# -------------------------------------------------------------------------- #


class Decoder:
    """Decoder."""

    def __init__(self, framer, encode=False):
        """Initialize a new instance of the decoder

        :param framer: The framer to use
        :param encode: If the message needs to be encoded
        """
        self.framer = framer
        self.encode = encode

    def decode(self, message):
        """Attempt to decode the supplied message

        :param message: The message to decode
        """
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
                    unit = decoder._header.get(  # pylint: disable=protected-access
                        "uid", 0x00
                    )
                    decoder.advanceFrame()
                    decoder.processIncomingPacket(message, self.report, unit)
                else:
                    self.check_errors(decoder, message)
            except Exception:  # pylint: disable=broad-except
                self.check_errors(decoder, message)

    def check_errors(self, decoder, message):
        """Attempt to find message errors

        :param message: The message to find errors in
        """
        txt = f"Unable to parse message - {message} with {decoder}"
        log.error(txt)

    def report(self, message):
        """Print the message information

        :param message: The message to print
        """
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
def get_options():
    """Parse the command line options

    :returns: The options manager
    """
    parser = OptionParser()

    parser.add_option(
        "-p",
        "--parser",
        help="The type of parser to use (tcp, rtu, binary, ascii)",
        dest="parser",
        default="tcp",
    )

    parser.add_option(
        "-D",
        "--debug",
        help="Enable debug tracing",
        action="store_true",
        dest="debug",
        default=False,
    )

    parser.add_option(
        "-m", "--message", help="The message to parse", dest="message", default=None
    )

    parser.add_option(
        "-a",
        "--ascii",
        help="The indicates that the message is ascii",
        action="store_true",
        dest="ascii",
        default=False,
    )

    parser.add_option(
        "-b",
        "--binary",
        help="The indicates that the message is binary",
        action="store_false",
        dest="ascii",
    )

    parser.add_option(
        "-f",
        "--file",
        help="The file containing messages to parse",
        dest="file",
        default=None,
    )

    parser.add_option(
        "-t",
        "--transaction",
        help="If the incoming message is in hexadecimal format",
        action="store_true",
        dest="transaction",
        default=False,
    )
    parser.add_option(
        "--framer",
        help="Framer to use",
        dest="framer",
        default=None,
    )

    (opt, arg) = parser.parse_args()

    if not opt.message and len(arg) > 0:
        opt.message = arg[0]

    return opt


def get_messages(option):
    """Do a helper method to generate the messages to parse

    :param options: The option manager
    :returns: The message iterator to parse
    """
    if option.message:
        if option.transaction:
            msg = ""
            for segment in option.message.split():
                segment = segment.replace("0x", "")
                segment = "0" + segment if len(segment) == 1 else segment
                msg = msg + segment
            option.message = msg

        if not option.ascii:
            option.message = c.decode(option.message.encode(), "hex_codec")
        yield option.message
    elif option.file:
        with open(option.file, "r") as handle:  # pylint: disable=unspecified-encoding
            for line in handle:
                if line.startswith("#"):
                    continue
                if not option.ascii:
                    line = line.strip()
                    line = line.decode("hex")
                yield line


def main():
    """Run main runner function"""
    option = get_options()

    if option.debug:
        try:
            log.setLevel(logging.DEBUG)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Logging is not supported on this system- {exc}")

    framer = {
        "tcp": ModbusSocketFramer,
        "rtu": ModbusRtuFramer,
        "binary": ModbusBinaryFramer,
        "ascii": ModbusAsciiFramer,
    }.get(option.framer or option.parser, ModbusSocketFramer)

    decoder = Decoder(framer, option.ascii)
    for message in get_messages(option):
        decoder.decode(message)


if __name__ == "__main__":
    main()
