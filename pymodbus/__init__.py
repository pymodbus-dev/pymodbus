"""Pymodbus: Modbus Protocol Implementation.

Released under the BSD license
"""

__all__ = [
    "ExceptionResponse",
    "Framer",
    "ModbusException",
    "pymodbus_apply_logging_config",
    "__version__",
    "__version_full__",
]

from pymodbus.exceptions import ModbusException
from pymodbus.framer import Framer
from pymodbus.logging import pymodbus_apply_logging_config
from pymodbus.pdu import ExceptionResponse


__version__ = "3.6.6"
__version_full__ = f"[pymodbus, version {__version__}]"
