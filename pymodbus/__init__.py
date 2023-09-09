"""Pymodbus: Modbus Protocol Implementation.

Released under the BSD license
"""

__all__ = [
    "pymodbus_apply_logging_config",
    "__version__",
    "__version_full__",
]

from pymodbus.logging import pymodbus_apply_logging_config


__version__ = "3.5.2"
__version_full__ = f"[pymodbus, version {__version__}]"
