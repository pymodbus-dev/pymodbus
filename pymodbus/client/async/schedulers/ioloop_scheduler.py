from __future__ import unicode_literals

from concurrent.futures import Future

from pymodbus.client.async.schedulers import Scheduler


class IOLoopScheduler(Scheduler):
    def __init__(self, io_loop=None):
        from tornado import ioloop
        self._ioloop = io_loop or ioloop.IOLoop.current()

    def schedule(self, method, *args, **kwargs):
        future = Future()

        def run():
            try:
                result = method(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

            future.done()

        self._ioloop.add_callback(run)

        return future
