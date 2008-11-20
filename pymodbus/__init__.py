'''
Pymodbus: Modbus Protocol implementation for Twisted Matrix

This package can supply modbus clients and servers:
	client:
	- Can perform single get/set on discretes and registers
	- Can perform multiple get/set on discretes and registers
	- Working on diagnostic/file/pipe/setting/info requets
	- Can fully scrape a host to be cloned

	server:
	- Can funtion as a fully implemented TCP modbus server
	- Working on creating server control context
	- Working on serial communication
	- Working on funtioning as a RTU/ASCII
	- Can mimic a server based on the supplied input data
   
TwistedModbus is built on top of the Pymodbus developed from code by:
	Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
	Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.
	Hynek Petrak <hynek@swac.cz>

Under the terms of the GPLv2 (with which the code was released) the
modified code is redistributed in full with the license affixed to
the new code.
'''

from pymodbus.version import version
__version__ = version.short()

#__all__ = [
#    "ReadBitsResponseBase", "ReadRegistersResponseBase",
#    "ParameterException", "ReadCoilsRequest", "ReadDiscreteInputsRequest",
#    "ReadHoldingRegistersRequest", "ReadInputRegistersRequest",
#    "WriteSingleCoilRequest", "WriteSingleRegisterRequest",
#    "ReadWriteMultipleRegistersRequest",
#    "ReadWriteMultipleRegistersResponse",
#    "WriteMultipleCoilsRequest", "WriteMultipleRegistersRequest",
#    "ExceptionResponse", "TCPMasterConnection",
#    "ModbusTCPServer", "ModbusServerContext"]
