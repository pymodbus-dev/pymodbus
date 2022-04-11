'''
Pymodbus: Modbus Protocol Implementation
-----------------------------------------

TwistedModbus is built on top of the code developed by:

    Copyright (c) 2001-2005 S.W.A.C. GmbH, Germany.
    Copyright (c) 2001-2005 S.W.A.C. Bohemia s.r.o., Czech Republic.
    Hynek Petrak <hynek@swac.cz>

Released under the the BSD license
'''

import logging as __logging
import pymodbus.version as __version
__version__ = __version.version.short()
__author__  = 'Galen Collins'
__maintainer__ = 'dhoomakethu'

#---------------------------------------------------------------------------#
# Block unhandled logging
#---------------------------------------------------------------------------#
try:
    from logging import NullHandler as __null
except ImportError:
    class __null(__logging.Handler): # pylint: disable=invalid-name
        def emit(self, record):
            pass

__logging.getLogger(__name__).addHandler(__null())
