#!/usr/bin/env python
"""
Modbus Message Parser
--------------------------------------------------------------------------

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
from __future__ import print_function
import collections
import textwrap
from optparse import OptionParser
import codecs as c

from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.transaction import ModbusBinaryFramer
from pymodbus.transaction import ModbusAsciiFramer
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.compat import  IS_PYTHON3
# -------------------------------------------------------------------------- #
# -------------------------------------------------------------------------- #
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()


# -------------------------------------------------------------------------- #
# build a quick wrapper around the framers
# -------------------------------------------------------------------------- #

class Decoder(object):

    def __init__(self, framer, encode=False):
        """ Initialize a new instance of the decoder

        :param framer: The framer to use
        :param encode: If the message needs to be encoded
        """
        self.framer = framer
        self.encode = encode

    def decode(self, message):
        """ Attempt to decode the supplied message

        :param message: The messge to decode
        """
        if IS_PYTHON3:
            value = message if self.encode else c.encode(message, 'hex_codec')
        else:
            value = message if self.encode else message.encode('hex')
        print("="*80)
        print("Decoding Message %s" % value)
        print("="*80)
        decoders = [
            self.framer(ServerDecoder(), client=None),
            self.framer(ClientDecoder(), client=None)
        ]
        for decoder in decoders:
            print("%s" % decoder.decoder.__class__.__name__)
            print("-"*80)
            try:
                decoder.addToFrame(message)
                if decoder.checkFrame():
                    unit = decoder._header.get("uid", 0x00)
                    decoder.advanceFrame()
                    decoder.processIncomingPacket(message, self.report, unit)
                else:
                    self.check_errors(decoder, message)
            except Exception as ex:
                self.check_errors(decoder, message)

    def check_errors(self, decoder, message):
        """ Attempt to find message errors

        :param message: The message to find errors in
        """
        log.error("Unable to parse message - {} with {}".format(message,
                                                                decoder))

    def report(self, message):
        """ The callback to print the message information

        :param message: The message to print
        """
        print("%-15s = %s" % ('name', message.__class__.__name__))
        for (k, v) in message.__dict__.items():
            if isinstance(v, dict):
                print("%-15s =" % k)
                for kk,vv in v.items():
                    print("  %-12s => %s" % (kk, vv))

            elif isinstance(v, collections.Iterable):
                print("%-15s =" % k)
                value = str([int(x) for x  in v])
                for line in textwrap.wrap(value, 60):
                    print("%-15s . %s" % ("", line))
            else:
                print("%-15s = %s" % (k, hex(v)))
        print("%-15s = %s" % ('documentation', message.__doc__))


# -------------------------------------------------------------------------- #
# and decode our message
# -------------------------------------------------------------------------- #
def get_options():
    """ A helper method to parse the command line options

    :returns: The options manager
    """
    parser = OptionParser()

    parser.add_option("-p", "--parser",
                      help="The type of parser to use "
                           "(tcp, rtu, binary, ascii)",
                      dest="parser", default="tcp")

    parser.add_option("-D", "--debug",
                      help="Enable debug tracing",
                      action="store_true", dest="debug", default=False)

    parser.add_option("-m", "--message",
                      help="The message to parse",
                      dest="message", default=None)

    parser.add_option("-a", "--ascii",
                      help="The indicates that the message is ascii",
                      action="store_true", dest="ascii", default=True)

    parser.add_option("-b", "--binary",
                      help="The indicates that the message is binary",
                      action="store_false", dest="ascii")

    parser.add_option("-f", "--file",
                      help="The file containing messages to parse",
                      dest="file", default=None)

    parser.add_option("-t", "--transaction",
                      help="If the incoming message is in hexadecimal format",
                      action="store_true", dest="transaction", default=False)

    (opt, arg) = parser.parse_args()

    if not opt.message and len(arg) > 0:
        opt.message = arg[0]

    return opt


def get_messages(option):
    """ A helper method to generate the messages to parse

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
            if not IS_PYTHON3:
                option.message = option.message.decode('hex')
            else:
                option.message = c.decode(option.message.encode(), 'hex_codec')
        yield option.message
    elif option.file:
        with open(option.file, "r") as handle:
            for line in handle:
                if line.startswith('#'): continue
                if not option.ascii:
                    line = line.strip()
                    line = line.decode('hex')
                yield line


def main():
    """ The main runner function
    """
    option = get_options()

    if option.debug:
        try:
            modbus_log.setLevel(logging.DEBUG)
            logging.basicConfig()
        except Exception as e:
            print("Logging is not supported on this system- {}".format(e))

    framer = lookup = {
        'tcp':    ModbusSocketFramer,
        'rtu':    ModbusRtuFramer,
        'binary': ModbusBinaryFramer,
        'ascii':  ModbusAsciiFramer,
    }.get(option.parser, ModbusSocketFramer)

    decoder = Decoder(framer, option.ascii)
    for message in get_messages(option):
        decoder.decode(message)


if __name__ == "__main__":
    main()
