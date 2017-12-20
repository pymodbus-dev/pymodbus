#!/usr/bin/env python
"""
Pymodbus Server Payload Example
--------------------------------------------------------------------------

If you want to initialize a server context with a complicated memory
layout, you can actually use the payload builder.
"""
# --------------------------------------------------------------------------- # 
# import the various server implementations
# --------------------------------------------------------------------------- # 
from pymodbus.server.sync import StartTcpServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

# --------------------------------------------------------------------------- # 
# import the payload builder
# --------------------------------------------------------------------------- # 

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

# --------------------------------------------------------------------------- # 
# configure the service logging
# --------------------------------------------------------------------------- # 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


def run_payload_server():
    # ----------------------------------------------------------------------- #
    # build your payload
    # ----------------------------------------------------------------------- #
    builder = BinaryPayloadBuilder(endian=Endian.Little)
    # builder.add_string('abcdefgh')
    # builder.add_32bit_float(22.34)
    # builder.add_16bit_uint(4660)
    # builder.add_8bit_int(18)
    builder.add_bits([0, 1, 0, 1, 1, 0, 1, 0])
    
    # ----------------------------------------------------------------------- #
    # use that payload in the data store
    # ----------------------------------------------------------------------- #
    # Here we use the same reference block for each underlying store.
    # ----------------------------------------------------------------------- #
    
    block = ModbusSequentialDataBlock(1, builder.to_registers())
    store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    context = ModbusServerContext(slaves=store, single=True)
    
    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/bashwork/pymodbus/'
    identity.ProductName = 'Pymodbus Server'
    identity.ModelName = 'Pymodbus Server'
    identity.MajorMinorRevision = '1.0'
    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    StartTcpServer(context, identity=identity, address=("localhost", 5020))
    

if __name__ == "__main__":
    run_payload_server()

