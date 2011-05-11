#!/usr/bin/env python
'''
This utility can be used to fully scrape a modbus device
and store its data as a Mobus Context for use with the
simulator.
'''

from twisted.internet import reactor

from pymodbus.client.async import ModbusClientFactory
from pymodbus.bit_read_message import ReadCoilsRequest
from pymodbus.bit_read_message import ReadDiscreteInputsRequest
from pymodbus.register_read_message import ReadHoldingRegistersRequest
from pymodbus.register_read_message import ReadInputRegistersRequest

from optparse import OptionParser
import pickle

#--------------------------------------------------------------------------#
# Logging
#--------------------------------------------------------------------------#
import logging
client_log = logging.getLogger("pymodbus.client")

#--------------------------------------------------------------------------#
# Helper Classes
#--------------------------------------------------------------------------#
class ClientException(Exception):
    ''' Exception for configuration error '''

    def __init__(self, string):
        Exception.__init__(self, string)
        self.string = string

    def __str__(self):
        return 'Client Error: %s' % self.string

class ClientScraper:
    ''' Exception for configuration error '''

    def __init__(self, host, port, address):
        '''
        Initializes the connection paramaters and requests
        @param host The host to connect to
        @param port The port the server resides on
        @param address The range to read to:from
        '''
        self.host = host

        if isinstance(port, int):
            self.port = port
        elif isinstance(port, str):
            self.port = int(port)

        self.requests = []
        for rqst in [
                ReadCoilsRequest,
                ReadDiscreteInputsRequest,
                ReadInputRegistersRequest,
                ReadHoldingRegistersRequest]:
            for i in range(*[int(j) for j in address.split(':')]):
                self.requests.append(rqst(i,1))

    def start(self):
        '''
        Starts the device scrape
        '''
        f = ModbusClientFactory(self.requests)
        self.p = reactor.connectTCP(self.host, self.port, f)

    def process(self, data):
        '''
        Starts the device scrape
        '''
        f = ModbusClientFactory(self.requests)
        self.p = reactor.connectTCP(self.host, self.port, f)

class ContextBuilder:
    '''
    This class is used to build our server datastore
    for use with the modbus simulator.
    '''

    def __init__(self, output):
        '''
        Initializes the ContextBuilder and checks data values
        @param file The output file for the server context
        '''
        try:
            self.file = open(output, "w")
        except Exception:
            raise ClientException("Unable to open file [%s]" % output)

    def build(self):
        ''' Builds the final output store file '''
        try:
            pass
            result = self.makeContext()
            pickle.dump(result, self.file)
            print("Device successfully scraped!")
        except Exception:
            raise ClientException("Invalid data")
        self.file.close()
        reactor.stop()

    def makeContext(self):
        ''' Builds the server context based on the passed in data '''
        # ModbusServerContext(d=sd, c=sc, h=sh, i=si)
        return "string"

#--------------------------------------------------------------------------#
# Main start point
#--------------------------------------------------------------------------#
def main():
    ''' Server launcher '''
    parser = OptionParser()
    parser.add_option("-o", "--output",
                    help="The resulting output file for the scrape",
                    dest="file", default="output.store")
    parser.add_option("-p", "--port",
                    help="The port to connect to",
                    dest="port", default="502")
    parser.add_option("-s", "--server",
                    help="The server to scrape",
                    dest="host", default="localhost")
    parser.add_option("-r", "--range",
                    help="The address range to scan",
                    dest="range", default="0:500")
    parser.add_option("-D", "--debug",
                    help="Enable debug tracing",
                    action="store_true", dest="debug", default=False)
    (opt, arg) = parser.parse_args()

    # enable debugging information
    if opt.debug:
        try:
            client_log.setLevel(logging.DEBUG)
    	    logging.basicConfig()
        except Exception as e:
    	    print("Logging is not supported on this system")

    # Begin scrape
    try:
        #ctx = ContextBuilder(opt.file)
        s = ClientScraper(opt.host, opt.port, opt.range)
        reactor.callWhenRunning(s.start)
        reactor.run()
    except ClientException as err:
        print(err)
        parser.print_help()

#---------------------------------------------------------------------------#
# Main jumper
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    main()
