"""Framer."""
__all__ = [
    "Framer",
    "FRAMER_NAME_TO_CLASS",
    "ModbusFramer",
    "ModbusAsciiFramer",
    "ModbusRtuFramer",
    "ModbusSocketFramer",
    "ModbusTlsFramer",
    "Framer",
    "FramerType",
]

from pymodbus.framer.framer import Framer, FramerType
from pymodbus.framer.old_framer_ascii import ModbusAsciiFramer
from pymodbus.framer.old_framer_base import ModbusFramer
from pymodbus.framer.old_framer_rtu import ModbusRtuFramer
from pymodbus.framer.old_framer_socket import ModbusSocketFramer
from pymodbus.framer.old_framer_tls import ModbusTlsFramer


FRAMER_NAME_TO_CLASS = {
    FramerType.ASCII: ModbusAsciiFramer,
    FramerType.RTU: ModbusRtuFramer,
    FramerType.SOCKET: ModbusSocketFramer,
    FramerType.TLS: ModbusTlsFramer,
}
