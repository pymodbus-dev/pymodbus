#!/usr/bin/env python
"""
Concurrent Modbus Client
---------------------------------------------------------------------------

This is an example of writing a high performance modbus client that allows
a high level of concurrency by using worker threads/processes to handle
writing/reading from one or more client handles at once.
"""
# -------------------------------------------------------------------------- #
# import system libraries
# -------------------------------------------------------------------------- #
import multiprocessing
import threading
import itertools
from collections import namedtuple

from pymodbus.compat import IS_PYTHON3

# we are using the future from the concurrent.futures released with
# python3. Alternatively we will try the backported library::
#   pip install futures
try:
    from concurrent.futures import Future
except ImportError:
    from futures import Future

# -------------------------------------------------------------------------- #
# import neccessary modbus libraries
# -------------------------------------------------------------------------- #
from pymodbus.client.common import ModbusClientMixin

# -------------------------------------------------------------------------- #
# configure the client logging
# -------------------------------------------------------------------------- #
import logging
log = logging.getLogger("pymodbus")
log.setLevel(logging.DEBUG)
logging.basicConfig()


# -------------------------------------------------------------------------- #
# Initialize out concurrency primitives
# -------------------------------------------------------------------------- #
class _Primitives(object):
    """ This is a helper class used to group the
    threading primitives depending on the type of
    worker situation we want to run (threads or processes).
    """

    def __init__(self, **kwargs):
        self.queue  = kwargs.get('queue')
        self.event  = kwargs.get('event')
        self.worker = kwargs.get('worker')

    @classmethod
    def create(cls, in_process=False):
        """ Initialize a new instance of the concurrency
        primitives.

        :param in_process: True for threaded, False for processes
        :returns: An initialized instance of concurrency primitives
        """
        if in_process:
            if IS_PYTHON3:
                from queue import Queue
            else:
                from Queue import Queue
            from threading import Thread
            from threading import Event
            return cls(queue=Queue, event=Event, worker=Thread)
        else:
            from multiprocessing import Queue
            from multiprocessing import Event
            from multiprocessing import Process
            return cls(queue=Queue, event=Event, worker=Process)


# -------------------------------------------------------------------------- #
# Define our data transfer objects
# -------------------------------------------------------------------------- #
# These will be used to serialize state between the various workers.
# We use named tuples here as they are very lightweight while giving us
# all the benefits of classes.
# -------------------------------------------------------------------------- #
WorkRequest  = namedtuple('WorkRequest',  'request, work_id')
WorkResponse = namedtuple('WorkResponse', 'is_exception, work_id, response')

# -------------------------------------------------------------------------- #
# Define our worker processes
# -------------------------------------------------------------------------- #
def _client_worker_process(factory, input_queue, output_queue, is_shutdown):
    """ This worker process takes input requests, issues them on its
    client handle, and then sends the client response (success or failure)
    to the manager to deliver back to the application.

    It should be noted that there are N of these workers and they can
    be run in process or out of process as all the state serializes.

    :param factory: A client factory used to create a new client
    :param input_queue: The queue to pull new requests to issue
    :param output_queue: The queue to place client responses
    :param is_shutdown: Condition variable marking process shutdown
    """
    log.info("starting up worker : %s", threading.current_thread())
    client = factory()
    while not is_shutdown.is_set():
        try:
            workitem = input_queue.get(timeout=1)
            log.debug("dequeue worker request: %s", workitem)
            if not workitem: continue
            try:
                log.debug("executing request on thread: %s", workitem)
                result = client.execute(workitem.request)
                output_queue.put(WorkResponse(False, workitem.work_id, result))
            except Exception as exception:
                log.exception("error in worker "
                              "thread: %s", threading.current_thread())
                output_queue.put(WorkResponse(True,
                                              workitem.work_id, exception))
        except Exception as ex:
            pass
    log.info("request worker shutting down: %s", threading.current_thread())


def _manager_worker_process(output_queue, futures, is_shutdown):
    """ This worker process manages taking output responses and
    tying them back to the future keyed on the initial transaction id.
    Basically this can be thought of as the delivery worker.

    It should be noted that there are one of these threads and it must
    be an in process thread as the futures will not serialize across
    processes..

    :param output_queue: The queue holding output results to return
    :param futures: The mapping of tid -> future
    :param is_shutdown: Condition variable marking process shutdown
    """
    log.info("starting up manager worker: %s", threading.current_thread())
    while not is_shutdown.is_set():
        try:
            workitem = output_queue.get()
            future = futures.get(workitem.work_id, None)
            log.debug("dequeue manager response: %s", workitem)
            if not future: continue
            if workitem.is_exception:
                future.set_exception(workitem.response)
            else: future.set_result(workitem.response)
            log.debug("updated future result: %s", future)
            del futures[workitem.work_id]
        except Exception as ex:
            log.exception("error in manager")
    log.info("manager worker shutting down: %s", threading.current_thread())


# -------------------------------------------------------------------------- #
# Define our concurrent client
# -------------------------------------------------------------------------- #
class ConcurrentClient(ModbusClientMixin):
    """ This is a high performance client that can be used
    to read/write a large number of reqeusts at once asyncronously.
    This operates with a backing worker pool of processes or threads
    to achieve its performance.
    """

    def __init__(self, **kwargs):
        """ Initialize a new instance of the client
        """
        worker_count = kwargs.get('count', multiprocessing.cpu_count())
        self.factory = kwargs.get('factory')
        primitives = _Primitives.create(kwargs.get('in_process', False))
        self.is_shutdown = primitives.event()  # process shutdown condition
        self.input_queue = primitives.queue()  # input requests to process
        self.output_queue = primitives.queue()  # output results to return
        self.futures = {}                 # mapping of tid -> future
        self.workers = []                 # handle to our worker threads
        self.counter = itertools.count()

        # creating the response manager
        self.manager = threading.Thread(
            target=_manager_worker_process,
            args=(self.output_queue, self.futures, self.is_shutdown)
        )
        self.manager.start()
        self.workers.append(self.manager)

        # creating the request workers
        for i in range(worker_count):
            worker = primitives.worker(
                target=_client_worker_process,
                args=(self.factory, self.input_queue, self.output_queue,
                      self.is_shutdown)
            )
            worker.start()
            self.workers.append(worker)

    def shutdown(self):
        """ Shutdown all the workers being used to 
        concurrently process the requests.
        """
        log.info("stating to shut down workers")
        self.is_shutdown.set()
        # to wake up the manager
        self.output_queue.put(WorkResponse(None, None, None))
        for worker in self.workers:
            worker.join()
        log.info("finished shutting down workers")

    def execute(self, request):
        """ Given a request, enqueue it to be processed
        and then return a future linked to the response
        of the call.

        :param request: The request to execute
        :returns: A future linked to the call's response
        """
        if IS_PYTHON3:
            fut, work_id = Future(), next(self.counter)
        else:
            fut, work_id = Future(), self.counter.next()
        self.input_queue.put(WorkRequest(request, work_id))
        self.futures[work_id] = fut
        return fut

    def execute_silently(self, request):
        """ Given a write request, enqueue it to
        be processed without worrying about calling the
        application back (fire and forget)

        :param request: The request to execute
        """
        self.input_queue.put(WorkRequest(request, None))


if __name__ == "__main__":
    from pymodbus.client.sync import ModbusTcpClient

    def client_factory():
        log.debug("creating client for: %s", threading.current_thread())
        client = ModbusTcpClient('127.0.0.1', port=5020)
        client.connect()
        return client

    client = ConcurrentClient(factory = client_factory)
    try:
        log.info("issuing concurrent requests")
        futures = [client.read_coils(i * 8, 8) for i in range(10)]
        log.info("waiting on futures to complete")
        for future in futures:
            log.info("future result: %s", future.result(timeout=1))
    finally:
        client.shutdown()
