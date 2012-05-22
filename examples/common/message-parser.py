#!/usr/bin/env python
'''
Pymodbus TCP Message Parser
--------------------------------------------------------------------------

The following is an example of how to parse modbus tcp messages
using the supplied framers.
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

    def __init__(self, framer):
        ''' Initialize a new instance of the decoder

        :param framer: The framer to use
        '''
        self.framer = framer

    def decode(self, message):
        ''' Attempt to decode the supplied message

        :param message: The messge to decode
        '''
        decoders = [
            self.framer(ServerDecoder()),
            self.framer(ClientDecoder()),
        ]
        for decoder in decoders:
            decoder.addToFrame(message)
            if decoder.checkFrame():
                decoder.advanceFrame()
                decoder.processIncomingPacket(message, self.report)
            else: self.check_errors(decoder, message)

    def check_errors(self, decoder, message):
        ''' Attempt to find message errors

        :param message: The message to find errors in
        '''
        pass

    def report(self, message):
        ''' The callback to print the message information

        :param message: The message to print
        '''
        print "-"*80
        print "Decoded Message"
        print "-"*80
        print "%-15s = %s" % ('name', message.__class__.__name__)
        for k,v in message.__dict__.items():
            if isinstance(v, collections.Iterable):
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
    parser = OptionParser()
    parser.add_option("-p", "--parser",
        help="The type of parser to use (tcp, rtu, binary, ascii)",
        dest="parser", default="tcp")
    parser.add_option("-D", "--debug",
        help="Enable debug tracing",
        action="store_true", dest="debug", default=False)
    parser.add_option("-m", "--message",
        help="The message to parse",
        dest="message", default="")
    (opt, arg) = parser.parse_args()

    return opt

def main():
    option = get_options()

    if option.debug:
        try:
            modbus_log.setLevel(logging.DEBUG)
    	    logging.basicConfig()
        except Exception, e:
    	    print "Logging is not supported on this system"

    framer = lookup = {
        'tcp':    ModbusSocketFramer,
        'rtc':    ModbusRtuFramer,
        'binary': ModbusBinaryFramer,
        'ascii':  ModbusAsciiFramer,
    }[option.parser]

    decoder = Decoder(framer)
    #decoder.decode(option.message)
    decoder.decode("\x00\x01\x12\x34\x00\x06\xff\x02\x01\x02\x00\x04")

if __name__ == "__main__":
    main()
