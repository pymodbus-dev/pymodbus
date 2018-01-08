import os
import time
from subprocess import Popen as execute
from twisted.internet.defer import Deferred

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
log = logging.getLogger(__name__)

class ContextRunner(object):
    """
    This is the base runner class for all the integration tests
    """
    __bit_functions = [2,1] # redundant are removed for now
    __reg_functions = [4,3] # redundant are removed for now

    def initialize(self, service=None):
        """ Initializes the test environment """
        if service:
            self.fnull   = open(os.devnull, 'w')
            self.service = execute(service, stdout=self.fnull, stderr=self.fnull)
            log.debug("%s service started: %s", service, self.service.pid)
            time.sleep(0.2)
        else: self.service = None
        log.debug("%s context started", self.context)

    def shutdown(self):
        """ Cleans up the test environment """
        try:
            if self.service:
                self.service.kill()
                self.fnull.close()
            self.context.reset()
        except: pass
        log.debug("%s context stopped" % self.context)

    def testDataContextRegisters(self):
        """ Test that the context gets and sets registers """
        address = 10
        values = [0x1234] * 32
        for fx in self.__reg_functions:
            self.context.setValues(fx, address, values)
            result = self.context.getValues(fx, address, len(values))
            self.assertEquals(len(result), len(values))
            self.assertEquals(result, values)

    def testDataContextDiscretes(self):
        """ Test that the context gets and sets discretes """
        address = 10
        values = [True] * 32
        for fx in self.__bit_functions:
            self.context.setValues(fx, address, values)
            result = self.context.getValues(fx, address, len(values))
            self.assertEquals(len(result), len(values))
            self.assertEquals(result, values)

