"""Pymodbus: Modbus Protocol Implementation.

Released under the BSD license
"""

__all__ = [
    "FramerType",
    "Log",
    "ModbusDeviceIdentification",
    "ModbusException",
    "ModbusIOException",
    "ModbusPdu",
    "__version__",
    "__version_full__",
    "pymodbus_apply_logging_config",
]

from .exceptions import ModbusException, ModbusIOException
from .framer import FramerType
from .logging import Log, pymodbus_apply_logging_config
from .pdu import ModbusDeviceIdentification, ModbusPdu


__version__ = "4.0.0dev17"
__version_full__ = f"[pymodbus, version {__version__}]"
