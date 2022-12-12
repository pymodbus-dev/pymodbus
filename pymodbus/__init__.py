"""Pymodbus: Modbus Protocol Implementation.

Released under the the BSD license
"""

import logging as __logging
from logging import NullHandler as __null

import pymodbus.version as __version


__version__ = __version.version.short()
__author__ = "Galen Collins"
__maintainer__ = "dhoomakethu, janiversen"

# ---------------------------------------------------------------------------#
#  Block unhandled logging
# ---------------------------------------------------------------------------#
__logging.getLogger(__name__).addHandler(__null())


def pymodbus_apply_logging_config(level=__logging.WARNING):
    """Apply basic logging configuration used by default by Pymodbus maintainers.

    Please call this function to format logging appropriately when opening issues.
    """
    __logging.basicConfig(
        format="%(asctime)s %(levelname)-5s %(module)s:%(lineno)s %(message)s",
        datefmt="%H:%M:%S",
        level=level,
    )
