#!/usr/bin/env python
'''
Pymodbus Performance Example
--------------------------------------------------------------------------

The following is an quick performance check of the synchronous
modbus client.
'''
#---------------------------------------------------------------------------# 
# import the necessary modules
#---------------------------------------------------------------------------# 
import logging, os
from time import time
from multiprocessing import log_to_stderr
from pymodbus.client.sync import ModbusTcpClient

#---------------------------------------------------------------------------# 
# choose between threads or processes
#---------------------------------------------------------------------------# 
#from multiprocessing import Process as Worker
from threading import Thread as Worker

#---------------------------------------------------------------------------# 
# initialize the test
#---------------------------------------------------------------------------# 
# Modify the parameters below to control how we are testing the client:
#
# * workers - the number of workers to use at once
# * cycles  - the total number of requests to send
# * host    - the host to send the requests to
#---------------------------------------------------------------------------# 
workers = 1
cycles  = 10000
host    = '127.0.0.1'


#---------------------------------------------------------------------------# 
# perform the test
#---------------------------------------------------------------------------# 
# This test is written such that it can be used by many threads of processes
# although it should be noted that there are performance penalties
# associated with each strategy.
#---------------------------------------------------------------------------# 
def single_client_test(host, cycles):
    ''' Performs a single threaded test of a synchronous
    client against the specified host

    :param host: The host to connect to
    :param cycles: The number of iterations to perform
    '''
    logger = log_to_stderr()
    logger.setLevel(logging.DEBUG)
    logger.debug("starting worker: %d" % os.getpid())

    try:
        count  = 0
        client = ModbusTcpClient(host)
        while count < cycles:
            result = client.read_holding_registers(10, 1).getRegister(0)
            count += 1
    except: logger.exception("failed to run test successfully")
    logger.debug("finished worker: %d" % os.getpid())

#---------------------------------------------------------------------------# 
# run our test and check results
#---------------------------------------------------------------------------# 
# We shard the total number of requests to perform between the number of
# threads that was specified. We then start all the threads and block on
# them to finish. This may need to switch to another mechanism to signal
# finished as the process/thread start up/shut down may skew the test a bit.
#---------------------------------------------------------------------------# 
args  = (host, int(cycles * 1.0 / workers))
procs = [Worker(target=single_client_test, args=args) for _ in range(workers)]
start = time()
any(p.start() for p in procs)   # start the workers
any(p.join()  for p in procs)   # wait for the workers to finish
stop  = time()
print "%d requests/second" % ((1.0 * cycles) / (stop - start))
