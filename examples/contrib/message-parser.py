#!/usr/bin/env python
'''
Modbus Message Parser
--------------------------------------------------------------------------

The following is an example of how to parse modbus messages
using the supplied framers for a number of protocols:

* tcp
* ascii
* rtu
* binary
'''
#---------------------------------------------------------------------------# 
# import needed libraries
#---------------------------------------------------------------------------# 
import sys
import collections
import textwrap
from optparse import OptionParser
from pymodbus.utilities import computeCRC, computeLRC
from pymodbus.factory import ClientDecoder, ServerDecoder
from pymodbus.transaction import ModbusSocketFramer
from pymodbus.transaction import ModbusBinaryFramer
from pymodbus.transaction import ModbusAsciiFramer
from pymodbus.transaction import ModbusRtuFramer

#--------------------------------------------------------------------------#
# Logging
#--------------------------------------------------------------------------#
import logging
modbus_log = logging.getLogger("pymodbus")


#---------------------------------------------------------------------------# 
# build a quick wrapper around the framers
#---------------------------------------------------------------------------# 
class Decoder(object):

    def __init__(self, framer, encode=False):
        ''' Initialize a new instance of the decoder

        :param framer: The framer to use
        :param encode: If the message needs to be encoded
        '''
        self.framer = framer
        self.encode = encode

    def decode(self, message):
        ''' Attempt to decode the supplied message

        :param message: The messge to decode
        '''
        value = message if self.encode else message.encode('hex')
        print "="*80
        print "Decoding Message %s" % value
        print "="*80
        decoders = [
            self.framer(ServerDecoder()),
            self.framer(ClientDecoder()),
        ]
        for decoder in decoders:
            print "%s" % decoder.decoder.__class__.__name__
            print "-"*80
            try:
                decoder.addToFrame(message)
                if decoder.checkFrame():
                    decoder.advanceFrame()
                    decoder.processIncomingPacket(message, self.report)
                else: self.check_errors(decoder, message)
            except Exception, ex: self.check_errors(decoder, message)

    def check_errors(self, decoder, message):
        ''' Attempt to find message errors

        :param message: The message to find errors in
        '''
        pass

    def report(self, message):
        ''' The callback to print the message information

        :param message: The message to print
        '''
        print "%-15s = %s" % ('name', message.__class__.__name__)
        for k,v in message.__dict__.iteritems():
            if isinstance(v, dict):
                print "%-15s =" % k
                for kk,vv in v.items():
                    print "  %-12s => %s" % (kk, vv)

            elif isinstance(v, collections.Iterable):
                print "%-15s =" % k
                value = str([int(x) for x  in v])
                for line in textwrap.wrap(value, 60):
                    print "%-15s . %s" % ("", line)
            else: print "%-15s = %s" % (k, hex(v))
        print "%-15s = %s" % ('documentation', message.__doc__)


#---------------------------------------------------------------------------# 
# and decode our message
#---------------------------------------------------------------------------# 
def get_options():
    ''' A helper method to parse the command line options

    :returns: The options manager
    '''
    parser = OptionParser()

    parser.add_option("-p", "--parser",
        help="The type of parser to use (tcp, rtu, binary, ascii)",
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

    (opt, arg) = parser.parse_args()

    if not opt.message and len(arg) > 0:
        opt.message = arg[0]

    return opt

def get_messages(option):
    ''' A helper method to generate the messages to parse

    :param options: The option manager
    :returns: The message iterator to parse
    '''
    if option.message:
        if not option.ascii:
            option.message = option.message.decode('hex')
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
    ''' The main runner function
    '''
    option = get_options()

    if option.debug:
        try:
            modbus_log.setLevel(logging.DEBUG)
    	    logging.basicConfig()
        except Exception, e:
    	    print "Logging is not supported on this system"

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
