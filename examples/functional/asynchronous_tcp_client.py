#!/usr/bin/env python
import unittest
from twisted.internet import reactor, protocol
from pymodbus.constants import Defaults
from pymodbus.client.async import ModbusClientProtocol
from base_runner import Runner

class AsynchronousTcpClient(Runner, unittest.TestCase):
    """
    These are the integration tests for the asynchronous
    tcp client.
    """

    def setUp(self):
        """ Initializes the test environment """
        def _callback(client): self.client = client
        self.initialize(["../tools/reference/diagslave", "-m", "tcp", "-p", "12345"])
        defer = protocol.ClientCreator(reactor, ModbusClientProtocol
                ).connectTCP("localhost", Defaults.Port)
        defer.addCallback(_callback)
        reactor.run()

    def tearDown(self):
        """ Cleans up the test environment """
        reactor.callLater(1, client.transport.loseConnection)
        reactor.callLater(2, reactor.stop)
        reactor.shutdown()

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
