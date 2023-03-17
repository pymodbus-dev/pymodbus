"""Pymodbus: Modbus Protocol Implementation.

Released under the BSD license
"""

__all__ = [
    "pymodbus_apply_logging_config",
    "__version__",
    "__version_full__",
]

from pymodbus.logging import pymodbus_apply_logging_config
from pymodbus.version import version


__version__ = version.short()
__version_full__ = str(version)
