import sys
from pymodbus.utilities import computeCRC
from pymodbus.transaction import ModbusTcpFramer
from pymodbus.factory import ClientDecoder, ServerDecoder

class Decoder(object):

    def decode(self, message):
        ''' Attempt to decode the supplied message

        :param message: The messge to decode
        '''
        decoders = [
            ModbusTcpFramer(ServerDecoder()),
            ModbusTcpFramer(ClientDecoder()),
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
            print "%-15s = %s" % (k, hex(v))
        print "%-15s = %s" % ('documentation', message.__doc__)

def main():
    if len(sys.argv) < 2:
        print "%s <message>" % sys.argv[0]
        sys.exit(-1)

    decoder = Decoder()
    #decoder.decode(sys.argv[1])
    #decoder.decode("\x00\x89\x90\xd6\x56")
    decoder.decode("\x00\x01\x00\x00\x00\x01\xfc\x1b")

if __name__ == "__main__":
    main()
