"""
Copyright (c) 2017 by Riptide I/O
All rights reserved.
"""
from __future__ import unicode_literals

from concurrent.futures.thread import ThreadPoolExecutor

from pymodbus.client.async.schedulers import Scheduler


class ThreadPoolScheduler(Scheduler):
    def __init__(self, max_workers=5):
        self._pool = ThreadPoolExecutor(max_workers=int(max_workers))

    def schedule(self, method, *args, **kwargs):
        return self._pool.submit(method, *args, **kwargs)
