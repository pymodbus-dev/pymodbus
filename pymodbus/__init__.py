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

from pymodbus.exceptions import ModbusException
from pymodbus.framer import FramerType
from pymodbus.logging import pymodbus_apply_logging_config
from pymodbus.pdu import ExceptionResponse
from pymodbus.pdu.device import ModbusDeviceIdentification


__version__ = "3.11.4"
__version_full__ = f"[pymodbus, version {__version__}]"
