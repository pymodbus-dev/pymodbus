"""Framer."""
__all__ = [
    "FRAMER_NAME_TO_OLD_CLASS",
    "ModbusFramer",
    "ModbusAsciiFramer",
    "ModbusRtuFramer",
    "ModbusSocketFramer",
    "ModbusTlsFramer",
    "AsyncFramer",
    "FramerType",
]

from pymodbus.framer.framer import AsyncFramer, FramerType
from pymodbus.framer.old_framer_ascii import ModbusAsciiFramer
from pymodbus.framer.old_framer_base import ModbusFramer
from pymodbus.framer.old_framer_rtu import ModbusRtuFramer
from pymodbus.framer.old_framer_socket import ModbusSocketFramer
from pymodbus.framer.old_framer_tls import ModbusTlsFramer


FRAMER_NAME_TO_OLD_CLASS = {
    FramerType.ASCII: ModbusAsciiFramer,
    FramerType.RTU: ModbusRtuFramer,
    FramerType.SOCKET: ModbusSocketFramer,
    FramerType.TLS: ModbusTlsFramer,
}
