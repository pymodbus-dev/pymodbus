from __future__ import unicode_literals

import abc


REACTOR = "reactor"
IO_LOOP = "io_loop"
ASYNC_IO = "async_io"


class Scheduler(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def schedule(self, method, *args, **kwargs):
        """
        Schedule the method to run asynchronously using the scheduler
        :param method: method to run
        :param args: args that needs to be passed to the method
        :param kwargs: kwargs that needs to be passed to the method

        :return: Future
        :rtype: concurrent.futures.Future
        """
