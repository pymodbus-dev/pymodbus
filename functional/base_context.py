import os
import time
from subprocess import Popen as execute
from twisted.internet.defer import Deferred

#---------------------------------------------------------------------------# 
# configure the client logging
#---------------------------------------------------------------------------# 
import logging
log = logging.getLogger(__name__)

class ContextRunner(object):
    '''
    This is the base runner class for all the integration tests
    '''

    def initialize(self, service):
        ''' Initializes the test environment '''
        log.debug("%s context started", self.context)

    def shutdown(self):
        ''' Cleans up the test environment '''
        #self.server.kill()
        try:
            self.contxt.reset()
        except: pass
        log.debug("special context stopped")

    def testSomething(self):
        pass

    def __validate(self, result, test):
        ''' Validate the result whether it is a result or a deferred.

        :param result: The result to __validate
        :param callback: The test to __validate
        '''
        if isinstance(result, Deferred):
            deferred.callback(lambda : self.assertTrue(test(result)))
            deferred.errback(lambda _: self.assertTrue(False))
        else: self.assertTrue(test(result))

