#!/usr/bin/env python3
# pylint: disable=missing-type-doc
"""Pymodbus Performance Example.

The following is an quick performance check of the synchronous
modbus client.
"""
# --------------------------------------------------------------------------- #
# import the necessary modules
# --------------------------------------------------------------------------- #
import logging
import os
from concurrent.futures import ThreadPoolExecutor as eWorker
from concurrent.futures import as_completed
from threading import Lock
from threading import Thread as tWorker
from time import time

from pymodbus.client import ModbusTcpClient


try:
    from multiprocessing import Process as mWorker
    from multiprocessing import log_to_stderr
except ImportError:
    log_to_stderr = logging.getLogger

# --------------------------------------------------------------------------- #
# choose between threads or processes
# --------------------------------------------------------------------------- #

# from multiprocessing import Process as Worker
# from threading import Thread as Worker
_thread_lock = Lock()
# --------------------------------------------------------------------------- #
# initialize the test
# --------------------------------------------------------------------------- #
# Modify the parameters below to control how we are testing the client:
#
# * workers - the number of workers to use at once
# * cycles  - the total number of requests to send
# * host    - the host to send the requests to
# --------------------------------------------------------------------------- #
workers = 10  # pylint: disable=invalid-name
cycles = 1000  # pylint: disable=invalid-name
host = "127.0.0.1"  # pylint: disable=invalid-name


# --------------------------------------------------------------------------- #
# perform the test
# --------------------------------------------------------------------------- #
# This test is written such that it can be used by many threads of processes
# although it should be noted that there are performance penalties
# associated with each strategy.
# --------------------------------------------------------------------------- #
def single_client_test(n_host, n_cycles):
    """Perform a single threaded test of a synchronous client against the specified host

    :param n_host: The host to connect to
    :param n_cycles: The number of iterations to perform
    """
    logger = log_to_stderr()
    logger.setLevel(logging.WARNING)
    txt = f"starting worker: {os.getpid()}"
    logger.debug(txt)

    try:
        count = 0
        client = ModbusTcpClient(n_host, port=5020)
        while count < n_cycles:
            client.read_holding_registers(10, 123, slave=1)
            count += 1
    except Exception:  # pylint: disable=broad-except
        logger.exception("failed to run test successfully")
    txt = f"finished worker: {os.getpid()}"
    logger.debug(txt)


def multiprocessing_test(func, extras):
    """Multiprocessing test."""
    start_time = time()
    procs = [mWorker(target=func, args=extras) for _ in range(workers)]

    any(p.start() for p in procs)  # start the workers
    any(p.join() for p in procs)  # wait for the workers to finish
    return start_time


def thread_test(func, extras):
    """Thread test."""
    start_time = time()
    procs = [tWorker(target=func, args=extras) for _ in range(workers)]

    any(p.start() for p in procs)  # start the workers
    any(p.join() for p in procs)  # wait for the workers to finish
    return start_time


def thread_pool_exe_test(func, extras):
    """Thread pool exe."""
    start_time = time()
    with eWorker(max_workers=workers, thread_name_prefix="Perform") as exe:
        futures = {exe.submit(func, *extras): job for job in range(workers)}
        for future in as_completed(futures):
            future.result()
    return start_time


# --------------------------------------------------------------------------- #
# run our test and check results
# --------------------------------------------------------------------------- #
# We shard the total number of requests to perform between the number of
# threads that was specified. We then start all the threads and block on
# them to finish. This may need to switch to another mechanism to signal
# finished as the process/thread start up/shut down may skew the test a bit.

# RTU 32 requests/second @9600
# TCP 31430 requests/second

# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    args = (host, int(cycles * 1.0 / workers))
    # with Worker(max_workers=workers, thread_name_prefix="Perform") as exe:
    #     futures = {exe.submit(single_client_test, *args): job for job in range(workers)}
    #     for future in as_completed(futures):
    #         data = future.result()
    # for _ in range(workers):
    #    futures.append(Worker.submit(single_client_test, args=args))
    # procs = [Worker(target=single_client_test, args=args)
    #          for _ in range(workers)]

    # any(p.start() for p in procs)   # start the workers
    # any(p.join() for p in procs)   # wait for the workers to finish
    # start = multiprocessing_test(single_client_test, args)
    # start = thread_pool_exe_test(single_client_test, args)
    for tester in (multiprocessing_test, thread_test, thread_pool_exe_test):
        print(tester.__name__)
        start = tester(single_client_test, args)
        stop = time()
        print(f"{(1.0 * cycles) / (stop - start)} requests/second")
        print(
            f"time taken to complete {cycles} cycle by "
            f"{workers} workers is {stop - start} seconds"
        )
        print()
