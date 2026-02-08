"""Pymodbus: Modbus Protocol Implementation.

Released under the BSD license
"""

__all__ = [
    "ExceptionResponse",
    "FramerType",
    "ModbusDeviceIdentification",
    "ModbusException",
    "__version__",
    "__version_full__",
    "pymodbus_apply_logging_config"
]

from .exceptions import ModbusException
from .framer import FramerType
from .logging import pymodbus_apply_logging_config
from .pdu import ExceptionResponse
from .pdu.device import ModbusDeviceIdentification


__version__ = "4.0.0dev8"
__version_full__ = f"[pymodbus, version {__version__}]"
