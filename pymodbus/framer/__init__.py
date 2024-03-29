"""Framer."""
__all__ = [
    "Framer",
    "FRAMER_NAME_TO_CLASS",
    "ModbusFramer",
    "ModbusAsciiFramer",
    "ModbusRtuFramer",
    "ModbusSocketFramer",
    "ModbusTlsFramer",
    "Framing",
    "FramerType",
]

from pymodbus.framer.framer import FramerType, Framing
from pymodbus.framer.old_framer_ascii import ModbusAsciiFramer
from pymodbus.framer.old_framer_base import ModbusFramer
from pymodbus.framer.old_framer_rtu import ModbusRtuFramer
from pymodbus.framer.old_framer_socket import ModbusSocketFramer
from pymodbus.framer.old_framer_tls import ModbusTlsFramer


Framer = FramerType


FRAMER_NAME_TO_CLASS = {
    Framer.ASCII: ModbusAsciiFramer,
    Framer.RTU: ModbusRtuFramer,
    Framer.SOCKET: ModbusSocketFramer,
    Framer.TLS: ModbusTlsFramer,
}
