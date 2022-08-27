"""Pymodbus: Modbus Protocol Implementation.

Released under the the BSD license
"""

import logging as __logging
from logging import NullHandler as __null

import pymodbus.version as __version


__version__ = __version.version.short()
__author__ = "Galen Collins"
__maintainer__ = "dhoomakethu"

# ---------------------------------------------------------------------------#
#  Block unhandled logging
# ---------------------------------------------------------------------------#
__logging.getLogger(__name__).addHandler(__null())
