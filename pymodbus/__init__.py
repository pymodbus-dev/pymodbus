"""
Pymodbus: Modbus Protocol Implementation
-----------------------------------------

This package can supply modbus clients and servers:

client:

- Can perform single get/set on discretes and registers
- Can perform multiple get/set on discretes and registers
- Working on diagnostic/file/pipe/setting/info requets
- Can fully scrape a host to be cloned

server:

- Can function as a fully implemented TCP modbus server
- Working on creating server control context
- Working on serial communication
- Working on funtioning as a RTU/ASCII
- Can mimic a server based on the supplied input data

TwistedModbus is built on top of the Pymodbus developed from code by:

    Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
    Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.
    Hynek Petrak <hynek@swac.cz>

Released under the the GPLv2
"""

from pymodbus.version import _version
__version__ = _version.short().split('+')[0]


#---------------------------------------------------------------------------#
# Block unhandled logging
#---------------------------------------------------------------------------#
import logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

h = NullHandler()
logging.getLogger("pymodbus").addHandler(h)

