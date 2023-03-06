"""Pymodbus: Modbus Protocol Implementation.

Released under the BSD license.
"""

from logging import WARNING

import pymodbus.version as __version
from pymodbus.logging import Log


__version__ = __version.version.short()
__author__ = "Galen Collins, Jan Iversen"
__maintainer__ = "dhoomakethu, janiversen"


def pymodbus_apply_logging_config(
    level: int = WARNING, **config_overrides: dict
) -> None:
    """Apply basic logging configuration.

    Please call this function to format logging appropriately when opening
    issues.  Default formatting is specified by the Pymodbus maintainers.
    """
    Log.apply_logging_config(level, **config_overrides)
