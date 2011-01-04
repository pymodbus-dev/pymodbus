#!/usr/bin/env python

#---------------------------------------------------------------------------# 
# the various server implementations
#---------------------------------------------------------------------------# 
from pymodbus.server.sync import StartTcpServer, StartUdpServer
from pymodbus.server.sync import StartSerialServer
from pymodbus.server.async import StartATcpServer, StartAUdpServer
from pymodbus.server.async import StartASerialServer

from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

#---------------------------------------------------------------------------# 
# configure the service logging
#---------------------------------------------------------------------------# 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#---------------------------------------------------------------------------# 
# initialize your data store
#---------------------------------------------------------------------------# 
store = ModbusSlaveContext(
    d = ModbusSequentialDataBlock(0, [1]*100),
    c = ModbusSequentialDataBlock(0, [1]*100),
    h = ModbusSequentialDataBlock(0, [1]*100),
    i = ModbusSequentialDataBlock(0, [1]*100))
context = ModbusServerContext(slaves=store, single=True)

#---------------------------------------------------------------------------# 
# run the server you want
#---------------------------------------------------------------------------# 
StartATcpServer(context)
#StartSerialServer(context, device='/dev/ptmx')
