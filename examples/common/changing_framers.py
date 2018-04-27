#!/usr/bin/env python
"""
Pymodbus Client Framer Overload
--------------------------------------------------------------------------

All of the modbus clients are designed to have pluggable framers
so that the transport and protocol are decoupled. This allows a user
to define or plug in their custom protocols into existing transports
(like a binary framer over a serial connection).

It should be noted that although you are not limited to trying whatever
you would like, the library makes no gurantees that all framers with
all transports will produce predictable or correct results (for example
tcp transport with an RTU framer). However, please let us know of any
success cases that are not documented!
"""
# --------------------------------------------------------------------------- #
# import the modbus client and the framers
# --------------------------------------------------------------------------- #
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

# --------------------------------------------------------------------------- #
# Import the modbus framer that you want
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
from pymodbus.transaction import ModbusSocketFramer as ModbusFramer
# from pymodbus.transaction import ModbusRtuFramer as ModbusFramer
#from pymodbus.transaction import ModbusBinaryFramer as ModbusFramer
#from pymodbus.transaction import ModbusAsciiFramer as ModbusFramer

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

if __name__ == "__main__":
    # ----------------------------------------------------------------------- #
    # Initialize the client
    # ----------------------------------------------------------------------- #
    client = ModbusClient('localhost', port=5020, framer=ModbusFramer)
    client.connect()

    # ----------------------------------------------------------------------- #
    # perform your requests
    # ----------------------------------------------------------------------- #
    rq = client.write_coil(1, True)
    rr = client.read_coils(1,1)
    assert(not rq.isError())     # test that we are not an error
    assert(rr.bits[0] == True)          # test the expected value

    # ----------------------------------------------------------------------- #
    # close the client
    # ---------------------------------------------------------------------- #
    client.close()
