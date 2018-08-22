#!/usr/bin/env python
"""
Pymodbus Asynchronous Processor Example
--------------------------------------------------------------------------

The following is a full example of a continuous client processor. Feel
free to use it as a skeleton guide in implementing your own.
"""
# --------------------------------------------------------------------------- #
# import the neccessary modules
# --------------------------------------------------------------------------- #
from twisted.internet import serialport, reactor
from twisted.internet.protocol import ClientFactory
from pymodbus.factory import ClientDecoder
from pymodbus.client.asynchronous.twisted import ModbusClientProtocol

# --------------------------------------------------------------------------- #
# Choose the framer you want to use
# --------------------------------------------------------------------------- #
# from pymodbus.transaction import ModbusBinaryFramer as ModbusFramer
# from pymodbus.transaction import ModbusAsciiFramer as ModbusFramer
from pymodbus.transaction import ModbusRtuFramer as ModbusFramer
# from pymodbus.transaction import ModbusSocketFramer as ModbusFramer

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger("pymodbus")
log.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# state a few constants
# --------------------------------------------------------------------------- #
SERIAL_PORT = "/tmp/ttyp0"
# --------------------------------------------------------------------------- #
STATUS_REGS = (1, 2)
STATUS_COILS = (1, 3)
CLIENT_DELAY = 1
UNIT = 0x01


# --------------------------------------------------------------------------- #
# an example custom protocol
# --------------------------------------------------------------------------- #
# Here you can perform your main procesing loop utilizing defereds and timed
# callbacks.
# --------------------------------------------------------------------------- #
class ExampleProtocol(ModbusClientProtocol):

    def __init__(self, framer, endpoint):
        """ Initializes our custom protocol

        :param framer: The decoder to use to process messages
        :param endpoint: The endpoint to send results to
        """
        ModbusClientProtocol.__init__(self, framer)
        self.endpoint = endpoint
        log.debug("Beginning the processing loop")
        reactor.callLater(CLIENT_DELAY, self.fetch_holding_registers)

    def fetch_holding_registers(self):
        """ Defer fetching holding registers
        """
        log.debug("Starting the next cycle")
        d = self.read_holding_registers(*STATUS_REGS, unit=UNIT)
        d.addCallbacks(self.send_holding_registers, self.error_handler)

    def send_holding_registers(self, response):
        """ Write values of holding registers, defer fetching coils

        :param response: The response to process
        """
        self.endpoint.write(response.getRegister(0))
        self.endpoint.write(response.getRegister(1))
        d = self.read_coils(*STATUS_COILS, unit=UNIT)
        d.addCallbacks(self.start_next_cycle, self.error_handler)

    def start_next_cycle(self, response):
        """ Write values of coils, trigger next cycle

        :param response: The response to process
        """
        self.endpoint.write(response.getBit(0))
        self.endpoint.write(response.getBit(1))
        self.endpoint.write(response.getBit(2))
        reactor.callLater(CLIENT_DELAY, self.fetch_holding_registers)

    def error_handler(self, failure):
        """ Handle any twisted errors

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
# It also persists data between client instances (think protocol singelton).
# --------------------------------------------------------------------------- #
class ExampleFactory(ClientFactory):

    protocol = ExampleProtocol

    def __init__(self, framer, endpoint):
        """ Remember things necessary for building a protocols """
        self.framer = framer
        self.endpoint = endpoint

    def buildProtocol(self, _):
        """ Create a protocol and start the reading cycle """
        proto = self.protocol(self.framer, self.endpoint)
        proto.factory = self
        return proto


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

    def __init__(self, factory, *args, **kwargs):
        """ Setup the client and start listening on the serial port

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
class LoggingLineReader(object):

    def write(self, response):
        """ Handle the next modbus response

        :param response: The response to process
        """
        log.info("Read Data: %d" % response)

# --------------------------------------------------------------------------- #
# start running the processor
# --------------------------------------------------------------------------- #
# This initializes the client, the framer, the factory, and starts the
# twisted event loop (the reactor). It should be noted that a number of
# things could be chanegd as one sees fit:
# - The ModbusRtuFramer could be replaced with a ModbusAsciiFramer
# - The SerialModbusClient could be replaced with reactor.connectTCP
# - The LineReader endpoint could be replaced with a database store
# --------------------------------------------------------------------------- #


def main():
    log.debug("Initializing the client")
    framer = ModbusFramer(ClientDecoder())
    reader = LoggingLineReader()
    factory = ExampleFactory(framer, reader)
    SerialModbusClient(factory, SERIAL_PORT, reactor)
    # factory = reactor.connectTCP("localhost", 502, factory)
    log.debug("Starting the client")
    reactor.run()


if __name__ == "__main__":
    main()

