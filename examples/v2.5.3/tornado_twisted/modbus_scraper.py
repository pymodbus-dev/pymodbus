#!/usr/bin/env python3
"""This is a simple scraper.

that can be pointed at a modbus device to pull down all its values and store
them as a collection of sequential data blocks.
"""
import logging
import pickle  # nosec
from optparse import OptionParser

from twisted.internet import (  # pylint: disable=import-error
    reactor,
    serialport,
)
from twisted.internet.protocol import (
    ClientFactory,  # pylint: disable=import-error
)

from pymodbus.client.asynchronous.twisted import ModbusClientProtocol
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext
from pymodbus.factory import ClientDecoder

# --------------------------------------------------------------------------- #
# Choose the framer you want to use
# --------------------------------------------------------------------------- #
# from pymodbus.transaction import ModbusBinaryFramer
# from pymodbus.transaction import ModbusAsciiFramer
# from pymodbus.transaction import ModbusRtuFramer
from pymodbus.transaction import ModbusSocketFramer


# -------------------------------------------------------------------------- #
# Configure the client logging
# -------------------------------------------------------------------------- #
log = logging.getLogger("pymodbus")


# --------------------------------------------------------------------------- #
# Define some constants
# --------------------------------------------------------------------------- #
COUNT = 8  # The number of bits/registers to read at once
DELAY = 0  # The delay between subsequent reads
SLAVE = 0x01  # The slave unit id to read from

# --------------------------------------------------------------------------- #
# A simple scraper protocol
# --------------------------------------------------------------------------- #
# I tried to spread the load across the device, but feel free to modify the
# logic to suit your own purpose.
# --------------------------------------------------------------------------- #


class ScraperProtocol(ModbusClientProtocol):
    """Scraper protocol."""

    address = None

    def __init__(self, framer, endpoint):
        """Initialize our custom protocol

        :param framer: The decoder to use to process messages
        :param endpoint: The endpoint to send results to
        """
        ModbusClientProtocol.__init__(self, framer)
        self.endpoint = endpoint

    def connection_made(self):
        """Call when the client has connected to the remote server."""
        super().connectionMade()
        log.debug("Beginning the processing loop")
        self.address = self.factory.starting
        reactor.callLater(DELAY, self.scrape_holding_registers)

    def connection_lost(self, reason):
        """Call when the client disconnects from the server.

        :param reason: The reason for the disconnection
        """
        reactor.callLater(DELAY, reactor.stop)

    def scrape_holding_registers(self):
        """Defer fetching holding registers"""
        txt = f"reading holding registers: {self.address}"
        log.debug(txt)
        data = self.read_holding_registers(self.address, count=COUNT, unit=SLAVE)
        data.addCallbacks(self.scrape_discrete_inputs, self.error_handler)

    def scrape_discrete_inputs(self, response):
        """Defer fetching holding registers"""
        txt = f"reading discrete inputs: {self.address}"
        log.debug(txt)
        self.endpoint.write((3, self.address, response.registers))
        data = self.read_discrete_inputs(self.address, count=COUNT, unit=SLAVE)
        data.addCallbacks(self.scrape_input_registers, self.error_handler)

    def scrape_input_registers(self, response):
        """Defer fetching holding registers"""
        txt = f"reading discrete inputs: {self.address}"
        log.debug(txt)
        self.endpoint.write((2, self.address, response.bits))
        data = self.read_input_registers(self.address, count=COUNT, unit=SLAVE)
        data.addCallbacks(self.scrape_coils, self.error_handler)

    def scrape_coils(self, response):
        """Write values of holding registers, defer fetching coils

        :param response: The response to process
        """
        txt = f"reading coils: {self.address}"
        log.debug(txt)
        self.endpoint.write((4, self.address, response.registers))
        data = self.read_coils(self.address, count=COUNT, unit=SLAVE)
        data.addCallbacks(self.start_next_cycle, self.error_handler)

    def start_next_cycle(self, response):
        """Write values of coils, trigger next cycle

        :param response: The response to process
        """
        txt = f"starting next round: {self.address}"
        log.debug(txt)
        self.endpoint.write((1, self.address, response.bits))
        self.address += COUNT
        if self.address >= self.factory.ending:
            self.endpoint.finalize()
            self.transport.loseConnection()
        else:
            reactor.callLater(DELAY, self.scrape_holding_registers)

    def error_handler(self, failure):
        """Handle any twisted errors

        :param failure: The error to handle
        """
        log.error(failure)


# --------------------------------------------------------------------------- #
# a factory for the example protocol
# --------------------------------------------------------------------------- #
# This is used to build client protocol's if you tie into twisted's method
# of processing. It basically produces client instances of the underlying
# protocol::
#
#     Factory(Protocol) -> ProtocolInstance
#
# It also persists data between client instances (think protocol singleton).
# --------------------------------------------------------------------------- #
class ScraperFactory(ClientFactory):  # pylint: disable=too-few-public-methods
    """Scraper factory."""

    protocol = ScraperProtocol

    def __init__(self, framer, endpoint, query):
        """Remember things necessary for building a protocols"""
        self.framer = framer
        self.endpoint = endpoint
        self.starting, self.ending = query

    def buildProtocol(self, _):  # pylint: disable=invalid-name
        """Create a protocol and start the reading cycle"""
        protocol = self.protocol(self.framer, self.endpoint)
        protocol.factory = self  # pylint: disable=attribute-defined-outside-init
        return protocol


# --------------------------------------------------------------------------- #
# a custom client for our device
# --------------------------------------------------------------------------- #
# Twisted provides a number of helper methods for creating and starting
# clients:
# - protocol.ClientCreator
# - reactor.connectTCP
#
# How you start your client is really up to you.
# --------------------------------------------------------------------------- #
class SerialModbusClient(serialport.SerialPort):
    """Serial modbus client."""

    def __init__(self, factory, *args, **kwargs):
        """Do setup the client and start listening on the serial port

        :param factory: The factory to build clients with
        """
        protocol = factory.buildProtocol(None)
        self.decoder = ClientDecoder()
        serialport.SerialPort.__init__(self, protocol, *args, **kwargs)


# --------------------------------------------------------------------------- #
# a custom endpoint for our results
# --------------------------------------------------------------------------- #
# An example line reader, this can replace with:
# - the TCP protocol
# - a context recorder
# - a database or file recorder
# --------------------------------------------------------------------------- #
class LoggingContextReader:
    """Logging context reader."""

    def __init__(self, output):
        """Initialize a new instance of the logger

        :param output: The output file to save to
        """
        self.output = output
        self.context = ModbusSlaveContext(
            di=ModbusSequentialDataBlock.create(),
            co=ModbusSequentialDataBlock.create(),
            hr=ModbusSequentialDataBlock.create(),
            ir=ModbusSequentialDataBlock.create(),
        )

    def write(self, response):
        """Handle the next modbus response

        :param response: The response to process
        """
        txt = f"Read Data: {str(response)}"
        log.info(txt)
        file_ptr, address, values = response
        self.context.setValues(file_ptr, address, values)

    def finalize(self):
        """Finalize."""
        with open(self.output, "w") as handle:
            pickle.dump(self.context, handle)


# -------------------------------------------------------------------------- #
# Main start point
# -------------------------------------------------------------------------- #
def get_options():
    """Parse the command line options

    :returns: The options manager
    """
    parser = OptionParser()

    parser.add_option(
        "-o",
        "--output",
        help="The resulting output file for the scrape",
        dest="output",
        default="datastore.pickle",
    )

    parser.add_option(
        "-p",
        "--port",
        help="The port to connect to",
        type="int",
        dest="port",
        default=502,
    )

    parser.add_option(
        "-s", "--server", help="The server to scrape", dest="host", default="127.0.0.1"
    )

    parser.add_option(
        "-r",
        "--range",
        help="The address range to scan",
        dest="query",
        default="0:1000",
    )

    parser.add_option(
        "-d",
        "--debug",
        help="Enable debug tracing",
        action="store_true",
        dest="debug",
        default=False,
    )

    (opt, _) = parser.parse_args()
    return opt


def main():
    """Run main runner function"""
    options = get_options()

    if options.debug:
        try:
            log.setLevel(logging.DEBUG)
        except Exception:
            print("Logging is not supported on this system")

    # split the query into a starting and ending range
    query = [int(p) for p in options.query.split(":")]

    try:
        log.debug("Initializing the client")
        framer = ModbusSocketFramer(ClientDecoder())
        reader = LoggingContextReader(options.output)
        factory = ScraperFactory(framer, reader, query)

        # how to connect based on TCP vs Serial clients
        if isinstance(framer, ModbusSocketFramer):
            reactor.connectTCP(options.host, options.port, factory)
        else:
            SerialModbusClient(factory, options.port, reactor)

        log.debug("Starting the client")
        reactor.run()
        log.debug("Finished scraping the client")
    except Exception as exc:
        print(exc)


# --------------------------------------------------------------------------- #
# Main jumper
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    main()
