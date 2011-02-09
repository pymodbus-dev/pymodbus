"""
Pymodbus: Modbus Protocol Implementation
-----------------------------------------

TwistedModbus is built on top of the code developed by:

    Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
    Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.
    Hynek Petrak <hynek@swac.cz>

Released under the the BSD license
"""

from pymodbus.version import _version
__version__ = _version.short()
__author__  = 'Galen Collins'


#---------------------------------------------------------------------------#
# Block unhandled logging
#---------------------------------------------------------------------------#
import logging
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

h = NullHandler()
logging.getLogger(__name__).addHandler(h)

