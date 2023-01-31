"""Pymodbus: Modbus Protocol Implementation.

Released under the the BSD license
"""

from logging import WARNING

import pymodbus.version as __version
from pymodbus.logging import Log


__version__ = __version.version.short()
__author__ = "Galen Collins"
__maintainer__ = "dhoomakethu, janiversen"


def pymodbus_apply_logging_config(level=WARNING):
    """Apply basic logging configuration used by default by Pymodbus maintainers.

    Please call this function to format logging appropriately when opening issues.
    """
    Log.apply_logging_config(level)
