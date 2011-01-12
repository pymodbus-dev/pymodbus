'''
Pymodbus Asynchrnonous Client Examples
--------------------------------------------------------------------------

The following is an example of how to use the asynchronous modbus
client implementation from pymodbus.
'''
#!/usr/bin/env python
#---------------------------------------------------------------------------# 
# import the various server implementations
#---------------------------------------------------------------------------# 
from pymodbus.client.async import ModbusTcpClient as ModbusClient
#from pymodbus.client.async import ModbusUdpClient as ModbusClient
#from pymodbus.client.async import ModbusSerialClient as ModbusClient

#---------------------------------------------------------------------------# 
# configure the client logging
#---------------------------------------------------------------------------# 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#---------------------------------------------------------------------------# 
# choose the client you want
#---------------------------------------------------------------------------# 
# make sure to start an implementation to hit against. For this
# you can use an existing device, the reference implementation in the tools
# directory, or start a pymodbus server.
#---------------------------------------------------------------------------# 
client = ModbusClient('127.0.0.1')

#---------------------------------------------------------------------------# 
# helper method to test deferred callbacks
#---------------------------------------------------------------------------# 
def dassert(deferred, callback):
    def _tester():
        assert(callback())
    deferred.callback(_tester)
    deferred.errback(lambda _: assert(False))

#---------------------------------------------------------------------------# 
# example requests
#---------------------------------------------------------------------------# 
# simply call the methods that you would like to use. An example session
# is displayed below along with some assert checks.
#---------------------------------------------------------------------------# 
rq = client.write_coil(1, True)
rr = client.read_coils(1,1)
dassert(rq, lambda r: r.function_code < 0x80)     # test that we are not an error
dassert(rr, lambda r: r.bits[0] == True)          # test the expected value

rq = client.write_coils(1, [True]*8)
rr = client.read_coils(1,8)
dassert(rq, lambda r: r.function_code < 0x80)     # test that we are not an error
dassert(rr, lambda r: r.bits == [True]*8)         # test the expected value

rq = client.write_coils(1, [False]*8)
rr = client.read_discrete_inputs(1,8)
dassert(rq, lambda r: r.function_code < 0x80)     # test that we are not an error
dassert(rr, lambda r: r.bits == [False]*8)        # test the expected value

rq = client.write_register(1, 10)
rr = client.read_holding_registers(1,1)
dassert(rq, lambda r: r.function_code < 0x80)     # test that we are not an error
dassert(rr, lambda r: r.registers[0] == 10)       # test the expected value

rq = client.write_registers(1, [10]*8)
rr = client.read_input_registers(1,8)
dassert(rq, lambda r: r.function_code < 0x80)     # test that we are not an error
dassert(rr, lambda r: r.registers == [10]*8)      # test the expected value

rq = client.readwrite_registers(1, [20]*8)
rr = client.read_input_registers(1,8)
dassert(rq, lambda r: r.function_code < 0x80)     # test that we are not an error
dassert(rr, lambda r: r.registers == [20]*8)      # test the expected value

#---------------------------------------------------------------------------# 
# close the client
#---------------------------------------------------------------------------# 
client.close()
