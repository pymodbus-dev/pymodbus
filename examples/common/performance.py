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
from pymodbus.client.sync import ModbusTcpClient
from time import time

#---------------------------------------------------------------------------# 
# initialize the test
#---------------------------------------------------------------------------# 
client = ModbusTcpClient('127.0.0.1')
count  = 0
start  = time()
iterations = 10000

#---------------------------------------------------------------------------# 
# perform the test
#---------------------------------------------------------------------------# 
while count < iterations:
    result = client.read_holding_registers(10, 1, 0).getRegister(0)
    count += 1

#---------------------------------------------------------------------------# 
# check our results
#---------------------------------------------------------------------------# 
stop = time()
print "%d requests/second" % ((1.0 * count) / (stop - start))

