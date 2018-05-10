import os
import time
from subprocess import Popen as execute
from twisted.internet.defer import Deferred

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
log = logging.getLogger(__name__)

class Runner(object):
    """
    This is the base runner class for all the integration tests
    """

    def initialize(self, service):
        """ Initializes the test environment """
        self.fnull  = open(os.devnull, 'w')
        self.server = execute(service, stdout=self.fnull, stderr=self.fnull)
        log.debug("%s service started: %s", service, self.server.pid)
        time.sleep(0.2)

    def shutdown(self):
        """ Cleans up the test environment """
        self.server.kill()
        self.fnull.close()
        log.debug("service stopped")

    def testReadWriteCoil(self):
        rq = self.client.write_coil(1, True)
        rr = self.client.read_coils(1,1)
        self._validate(rq, lambda r: not r.isError())
        self._validate(rr, lambda r: r.bits[0] == True)

    def testReadWriteCoils(self):
        rq = self.client.write_coils(1, [True]*8)
        rr = self.client.read_coils(1,8)
        self._validate(rq, lambda r: not r.isError())
        self._validate(rr, lambda r: r.bits == [True]*8)

    def testReadWriteDiscreteRegisters(self):
        rq = self.client.write_coils(1, [False]*8)
        rr = self.client.read_discrete_inputs(1,8)
        self._validate(rq, lambda r: not r.isError())
        self._validate(rr, lambda r: r.bits == [False]*8)

    def testReadWriteHoldingRegisters(self):
        rq = self.client.write_register(1, 10)
        rr = self.client.read_holding_registers(1,1)
        self._validate(rq, lambda r: not r.isError())
        self._validate(rr, lambda r: r.registers[0] == 10)

    def testReadWriteInputRegisters(self):
        rq = self.client.write_registers(1, [10]*8)
        rr = self.client.read_input_registers(1,8)
        self._validate(rq, lambda r: not r.isError())
        self._validate(rr, lambda r: r.registers == [10]*8)

    def testReadWriteRegistersTogether(self):
        arguments = {
            'read_address':    1,
            'read_count':      8,
            'write_address':   1,
            'write_registers': [20]*8,
        }
        rq = self.client.readwrite_registers(**arguments)
        rr = self.client.read_input_registers(1,8)
        self._validate(rq, lambda r: not r.isError())
        self._validate(rr, lambda r: r.registers == [20]*8)

    def _validate(self, result, test):
        """ Validate the result whether it is a result or a deferred.

        :param result: The result to _validate
        :param callback: The test to _validate
        """
        if isinstance(result, Deferred):
            deferred.callback(lambda : self.assertTrue(test(result)))
            deferred.errback(lambda _: self.assertTrue(False))
        else: self.assertTrue(test(result))

